"""
T1:
start_of_measurement

T2:
SignalManipulation.healthVector_rightCamPreProcUnreliable = 1

ET2:
delay -0.1s:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == {CORE_INIT} (0)
AP.CtrlCommandPort.stdRequest_nu == {STD_REQ_INIT} (1)

delay 0.1s:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == {CORE_ERROR} (5)
AP.CtrlCommandPort.stdRequest_nu == {STD_REQ_ERROR} (9)
AP.psmDebugPort.stateVarESM_nu == {ESM_IRREVERSIBLE_ERROR} (3)
"""

"""import libraries"""
import logging
import os
import sys

import numpy as np
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
from pl_parking.PLP.MF.AUP.SWRT_CNC_AUP_ManeuveringState_CancelAVG import convert_dict_to_pandas
from pl_parking.PLP.MF.constants import AUPConstants as aup

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_104_Req_2325977_2326001"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        RIGHT_CAM = "SignalManipulation.healthVector_rightCamPreProcUnreliable"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        STD_REQ = "AP.CtrlCommandPort.stdRequest_nu"
        VAR_ESM = "AP.psmDebugPort.stateVarESM_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.RIGHT_CAM: [
                "SignalManipulation.healthVector_rightCamPreProcUnreliable",
            ],
            self.Columns.CORE_STATE: [
                "AP.PARKSMCoreStatusPort.parksmCoreState_nu",
            ],
            self.Columns.STD_REQ: [
                "AP.CtrlCommandPort.stdRequest_nu",
            ],
            self.Columns.VAR_ESM: [
                "AP.psmDebugPort.stateVarESM_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 104 Req 2325977 2326001",
    description=(
        "This test case verifies that in case the Automated Parking Core is in Init state and the Health Vector reports an AUP irreversible error \
            (right camera pre-processing is unreliable) then the Automated Parking Core shall transition to Error state."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_104_Req_2325977_2326001_TS(TestStep):
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

    #
    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """  # required docstring
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        try:
            time_threshold_2 = None

            eval_cond_1 = False
            evaluation_1 = ""

            # signal_name = signals_obj._properties
            # Make a constant with the reader for signals:
            self.test_result = fc.INPUT_MISSING  # Result
            self.result.measured_result = DATA_NOK  # Initializing the result with data nok
            # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)

            signal_summary = {}  # Initializing the dictionary with data for final evaluation table

            signals = self.readers[ALIAS]
            signals[Signals.Columns.TIMESTAMP] = signals.index

            time = signals[Signals.Columns.TIME]
            right_cam = signals[Signals.Columns.RIGHT_CAM]
            core_state = signals[Signals.Columns.CORE_STATE]
            std_req = signals[Signals.Columns.STD_REQ]
            var_esm = signals[Signals.Columns.VAR_ESM]

            signals["status_core_state"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_std_req"] = std_req.apply(lambda x: fh.get_status_label(x, aup.STD_REQUEST))
            signals["status_var_esm"] = var_esm.apply(lambda x: fh.get_status_label(x, aup.ESM_STATE))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(right_cam, 1)

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when the <br>"
                    f"signal {Signals.Columns.RIGHT_CAM} == 1:<br>"
                    f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_2 - 10]} ({core_state.iloc[time_threshold_2 - 10]}) <br>"
                    f"- the signal {Signals.Columns.STD_REQ} == {signals['status_std_req'].iloc[time_threshold_2 - 10]} ({std_req.iloc[time_threshold_2 - 10]}) <br>"
                    f"AND <b>after</b> that timestamp:<br>"
                    f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_2 + 10]} ({core_state.iloc[time_threshold_2 + 10]}) <br>"
                    f"- the signal {Signals.Columns.STD_REQ} == {signals['status_std_req'].iloc[time_threshold_2 + 10]} ({std_req.iloc[time_threshold_2 + 10]}) <br>"
                    f"- the signal {Signals.Columns.VAR_ESM} == {signals['status_var_esm'].iloc[time_threshold_2 + 10]} ({var_esm.iloc[time_threshold_2 + 10]}) <br><br>"
                    f"This confirms that the Automated Parking Core transitioned from Init to Error when the Health <br>\
                        Vector reported an AUP irreversible error.".split()
                )
                eval_cond_1 = True

                delay_neg_core = core_state.iloc[time_threshold_2 - 10] != aup.CORE_STATUS.CORE_INIT
                delay_neg_std = std_req.iloc[time_threshold_2 - 10] != aup.STD_REQUEST.STD_REQ_INIT

                delay_pos_core = core_state.iloc[time_threshold_2 + 10] != aup.CORE_STATUS.CORE_ERROR
                delay_pos_std = std_req.iloc[time_threshold_2 + 10] != aup.STD_REQUEST.STD_REQ_ERROR
                delay_pos_var = var_esm.iloc[time_threshold_2 + 10] != aup.ESM_STATE.ESM_IRREVERSIBLE_ERROR

                if delay_neg_core or delay_neg_std:
                    evaluation_1 = " ".join(
                        f"The evaluation is FAILED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when the <br>"
                        f"signal {Signals.Columns.RIGHT_CAM} == 1:<br>"
                        f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_2 - 10]} ({core_state.iloc[time_threshold_2 - 10]}) <br>"
                        f"- the signal {Signals.Columns.STD_REQ} == {signals['status_std_req'].iloc[time_threshold_2 - 10]} ({std_req.iloc[time_threshold_2 - 10]}) <br><br>"
                        f"This means that the Automated Parking Core wasn't in Init state before the Health Vector reported an AUP irreversible error.".split()
                    )
                    eval_cond_1 = False

                elif delay_pos_core or delay_pos_std or delay_pos_var:
                    evaluation_1 = " ".join(
                        f"The evaluation is FAILED because <b>after</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when the <br>"
                        f"signal {Signals.Columns.RIGHT_CAM} == 1:<br>"
                        f"- the signal {Signals.Columns.CORE_STATE} == {signals['status_core_state'].iloc[time_threshold_2 + 10]} ({core_state.iloc[time_threshold_2 + 10]}) <br>"
                        f"- the signal {Signals.Columns.STD_REQ} == {signals['status_std_req'].iloc[time_threshold_2 + 10]} ({std_req.iloc[time_threshold_2 + 10]}) <br>"
                        f"- the signal {Signals.Columns.VAR_ESM} == {signals['status_var_esm'].iloc[time_threshold_2 + 10]} ({var_esm.iloc[time_threshold_2 + 10]}) <br><br>"
                        f"This means that the Automated Parking Core didn't transition from Init to Error state after <br>\
                                the Health Vector reported an AUP irreversible error.".split()
                    )
                    eval_cond_1 = False

            else:
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger {Signals.Columns.RIGHT_CAM} == 1 was never found.".split()
                )

            if eval_cond_1:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            expected_val_1 = "delay -0.1:<br>\
                AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_INIT (0)<br>\
                AP.CtrlCommandPort.stdRequest_nu == STD_REQ_INIT (1)<br>\
                delay 0.1:<br>\
                AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_ERROR (5)<br>\
                AP.CtrlCommandPort.stdRequest_nu == STD_REQ_ERROR (9)<br>\
                AP.psmDebugPort.stateVarESM_nu == ESM_IRREVERSIBLE_ERROR (3)"

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T2"] = [expected_val_1, evaluation_1, verdict1]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=right_cam,
                    mode="lines",
                    name=Signals.Columns.RIGHT_CAM,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=core_state,
                    mode="lines",
                    name=Signals.Columns.CORE_STATE,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_core_state"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=std_req,
                    mode="lines",
                    name=Signals.Columns.STD_REQ,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_std_req"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=var_esm,
                    mode="lines",
                    name=Signals.Columns.VAR_ESM,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_var_esm"],
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Time[s]",
                title=" Graphical Overview",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            if time_threshold_2 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_2],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T2",
                )
            plots.append(fig)
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


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="SWRT_CNC_AUP_ManeuveringState_Table_104_Req_2325977_2326001",
    description=(
        "This test case verifies that in case the Automated Parking Core is in Init state and the Health Vector reports an AUP irreversible error \
            (right camera pre-processing is unreliable) then the Automated Parking Core shall transition to Error state."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_104_Req_2325977_2326001_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_104_Req_2325977_2326001_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br>
                T1: start_of_measurement <br>
                T2: <br>
                    <em>SignalManipulation.healthVector_rightCamPreProcUnreliable</em> == 1 <br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T2: <br>
                delay -0.1s: <br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_INIT (0)<br>
                    <em>AP.CtrlCommandPort.stdRequest_nu</em> == STD_REQ_INIT (1)<br>
                delay 0.1s: <br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_ERROR (5)<br>
                    <em>AP.CtrlCommandPort.stdRequest_nu</em> == STD_REQ_ERROR (9)<br>
                    <em>AP.psmDebugPort.stateVarESM_nu</em> == ESM_IRREVERSIBLE_ERROR (3)
            </td>
        </tr>
    </table>

"""
