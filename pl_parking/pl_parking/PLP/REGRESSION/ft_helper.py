"""
This module provides helper functions and classes for regression testing in the PLP project.
Functions:
    get_port_status(signal_status):
        Method to give a signal status with verdict and color.
Classes:
    BaseStepRregressionTS(TestStep):
        A class to handle the base step regression test step.
        Methods:
            __init__():
                Initialize the test step.
            process(**kwargs):
                Process the test step with given keyword arguments.
"""

import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
from tsf.core.results import DATA_NOK, FALSE, TRUE
from tsf.core.testcase import TestStep

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

"""imports from current repo"""
import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.REGRESSION.constants as constants
from pl_parking.PLP.MF.constants import PlotlyTemplate

__author__ = "Dana Frunza"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

VALID_PASS_RATE = 0.95

text_dict = {
    0: "NOT INITIALIZED (0)",  # signal is not valid
    1: "VALID (1)",
    2: "INVALID (2)",  # signal is not valid
}


def get_port_status(signal_status):
    """Method to give a signal status with verdict and color."""
    bg_color = ""
    message = ""
    EVAL_PASSED = 0
    EVAL_FAILED = 1
    eval_status = EVAL_PASSED
    color_dict = {
        0: "#7F7F7F",  # signal is not valid
        1: "#28a745",
        2: "#dc3545",
    }

    count_valid_values = 0
    for index in signal_status:
        if index == constants.ComponentSigStatus.AL_SIG_STATE_OK:
            count_valid_values = count_valid_values + 1

    """Sig Status evaluation is passed if Sig Status is AL_SIG_STATE_OK more then 95%"""
    if count_valid_values / len(signal_status) > VALID_PASS_RATE:
        bg_color = color_dict[constants.ComponentSigStatus.AL_SIG_STATE_OK]
        message = text_dict[constants.ComponentSigStatus.AL_SIG_STATE_OK]
        eval_status = EVAL_PASSED
    elif any(signal_status == constants.ComponentSigStatus.AL_SIG_STATE_INVALID):
        bg_color = color_dict[constants.ComponentSigStatus.AL_SIG_STATE_INVALID]
        message = text_dict[constants.ComponentSigStatus.AL_SIG_STATE_INVALID]
        eval_status = EVAL_FAILED
    elif all(signal_status == constants.ComponentSigStatus.AL_SIG_STATE_INIT):
        bg_color = color_dict[constants.ComponentSigStatus.AL_SIG_STATE_INIT]
        message = text_dict[constants.ComponentSigStatus.AL_SIG_STATE_INIT]
        eval_status = EVAL_FAILED
    else:
        bg_color = color_dict[constants.ComponentSigStatus.AL_SIG_STATE_INVALID]
        message = "Not Valid values"
        eval_status = EVAL_FAILED
    return (
        (
            f'<span align="center" style="width: 100%; height: 100%; display: block;background-color: {bg_color}'
            f' ; color : #ffffff">{message}</span>'
        ),
        eval_status,
    )


class BaseStepRregressionTS(TestStep):
    """A class to handle the base step regression test step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the teststep with given keyword arguments."""
        try:
            _log.debug("Starting processing...")
            # Update the details from the results page with the needed information
            # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)

            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok

            signals_obj = kwargs["signals_obj"]
            remark = kwargs.get("remark", "Check eSigStatus for signals.")
            table_title = (
                f"Check if the signals have {text_dict[1]} values at least {VALID_PASS_RATE*100}% of the time."
            )
            signals = kwargs["signals"]
            signal_names = kwargs["signal_names"]
            for val in signals_obj._properties.values():
                if isinstance(val, list):
                    for sig, _ in enumerate(val):
                        if val[sig].startswith("."):
                            if len(signals_obj._root) == 1:
                                val[sig] = signals_obj._root[0] + val[sig]
            port_status = []
            eval_status = []
            for signal in signal_names:
                try:
                    port, eval = get_port_status(signals[signal])
                except KeyError:
                    port, eval = (
                        (
                            '<span align="center" style="width: 100%; height: 100%; display: block;background-color: #ffc107'
                            ' ; color : #ffffff">INPUT MISSING: Signal not present.</span>'
                        ),
                        -1,
                    )
                port_status.append(port)
                eval_status.append(eval)

            if any(eval_status) and not all([x == -1 for x in eval_status]):

                self.test_result = fc.FAIL
                self.result.measured_result = FALSE
                ratio = round((len([x for x in eval_status if x != 0]) / len(eval_status) * 100), 2)
            elif all([x == -1 for x in eval_status]):
                self.test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                ratio = 0
            else:
                self.test_result = fc.PASS
                self.result.measured_result = TRUE
                ratio = round((eval_status.count(0) / len(eval_status) * 100), 2)

            self.result.details["Result_ratio"] = ratio
            sigStatusTable = pd.DataFrame(
                {
                    "Signal evaluated": {
                        str(k): signals_obj._properties[signal_names[k]][0] for k in range(len(port_status))
                    },
                    "Port Status": {str(k): port_status[k] for k in range(len(port_status))},
                }
            )

            sigStatusTable = fh.build_html_table(sigStatusTable, remark, table_title)

            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.plots.append(sigStatusTable)

            fig = go.Figure()
            # add the needed signals in the plot
            for sg in signal_names:
                try:
                    fig.add_trace(
                        go.Scatter(
                            x=signals.index.values.tolist(), y=signals[sg].values.tolist(), mode="lines", name=sg
                        )
                    )
                except KeyError:
                    print(f"Signal {sg} not found in the signals DataFrame.")

            fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[epoch]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt, showlegend=True)
            self.plots.append(fig)
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
