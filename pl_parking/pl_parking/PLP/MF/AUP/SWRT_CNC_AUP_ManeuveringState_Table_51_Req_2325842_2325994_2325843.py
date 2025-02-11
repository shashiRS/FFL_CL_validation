"""
T1:
start_of_measurement

T2: // front camera becomes unreliable
SignalManipulation.healthVector_frontCamVisionUnreliable = 1

T3: // heal condition
SignalManipulation.healthVector_frontCamVisionUnreliable = 0

T4: // turn off the engine
SignalManipulation.additionalBCMStatusPort_ignitionOn_nu = 0

T5: // turn on the engine
SignalManipulation.additionalBCMStatusPort_ignitionOn_nu = 1

ET2:
delay -0.1s: // before the error condition, the system had no errors
AP.PARKSMCoreStatusPort.parksmCoreState_nu != CORE_ERROR  (5)
AP.psmDebugPort.stateVarESM_nu == ESM_NO_ERROR (1)

delay 0.1s:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_ERROR  (5)
AP.psmDebugPort.stateVarESM_nu == ESM_IRREVERSIBLE_ERROR (3)
AP.apUserInformationPort.generalUserInformation_nu == FRONT_CAM_VISION_UNRELIABLE (43)

INT_ET2_ET4:
delay -0.1:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_ERROR (5)

ET5: // check that the system is transitioning to INIT after an ignition cycle
delay 0.1s:
AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_INIT (0)
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
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_51_Req_2325842_2325994_2325843"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        FRONT_CAM = "SignalManipulation.healthVector_frontCamVisionUnreliable"
        IGN_ON = "SignalManipulation.additionalBCMStatusPort_ignitionOn_nu"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        VAR_ESM = "AP.psmDebugPort.stateVarESM_nu"
        USER_INF = "AP.apUserInformationPort.generalUserInformation_nu"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LSCA", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
            ],
            self.Columns.FRONT_CAM: [
                "SignalManipulation.healthVector_frontCamVisionUnreliable",
            ],
            self.Columns.IGN_ON: [
                "SignalManipulation.additionalBCMStatusPort_ignitionOn_nu",
            ],
            self.Columns.CORE_STATE: [
                "AP.PARKSMCoreStatusPort.parksmCoreState_nu",
            ],
            self.Columns.VAR_ESM: [
                "AP.psmDebugPort.stateVarESM_nu",
            ],
            self.Columns.USER_INF: [
                "AP.apUserInformationPort.generalUserInformation_nu",
            ],
        }


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Maneuvering State Table 51 Req 2325842 2325994 2325843",
    description=(
        "This test case verifies that if AUPCore receives the information that the front camera vision is unreliable, which is \
            an irreversible error, AUPCore shall go into error state and stay in this state until the ignition is switched off.\
                Also, information about the reason of the error shall be provided by AUPCore."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_51_Req_2325842_2325994_2325843_TS(TestStep):
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
            time_threshold_3 = None
            time_threshold_4 = None
            time_threshold_5 = None

            eval_cond_1 = False
            eval_cond_2 = False
            eval_cond_3 = False
            evaluation_1 = ""
            evaluation_2 = ""
            evaluation_3 = ""

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
            front_cam = signals[Signals.Columns.FRONT_CAM]
            ign_on = signals[Signals.Columns.IGN_ON]
            core_state = signals[Signals.Columns.CORE_STATE]
            var_esm = signals[Signals.Columns.VAR_ESM]
            user_inf = signals[Signals.Columns.USER_INF]

            signals["status_ign_on"] = ign_on.apply(lambda x: "Ignition ON" if x == 1 else "Ignition OFF")
            signals["status_core_state"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_var_esm"] = var_esm.apply(lambda x: fh.get_status_label(x, aup.ESM_STATE))
            signals["status_user_inf"] = user_inf.apply(lambda x: fh.get_status_label(x, aup.HMI_MESSAGE))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(front_cam, 1)
            time_threshold_3 = find_time_threshold(front_cam.iloc[time_threshold_2:], 0) + time_threshold_2
            time_threshold_4 = find_time_threshold(ign_on.iloc[time_threshold_3:], 0) + time_threshold_3
            time_threshold_5 = find_time_threshold(ign_on.iloc[time_threshold_4:], 1) + time_threshold_4

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when "
                    f"the signal <b>{Signals.Columns.FRONT_CAM}</b> == 1: <br>"
                    f"- the signal {Signals.Columns.CORE_STATE} is in {signals['status_core_state'].iloc[time_threshold_2 - 10]} ({core_state.iloc[time_threshold_2 - 10]}) state<br>"
                    f"- and the signal {Signals.Columns.VAR_ESM} is in {signals['status_var_esm'].iloc[time_threshold_2 - 10]} ({var_esm.iloc[time_threshold_2 - 10]}) state<br>"
                    f"AND <b>after</b> that timestamp:<br>"
                    f"- the signal {Signals.Columns.CORE_STATE} is in {signals['status_core_state'].iloc[time_threshold_2 + 10]} ({core_state.iloc[time_threshold_2 + 10]}) state<br>"
                    f"- and the signal {Signals.Columns.VAR_ESM} is in {signals['status_var_esm'].iloc[time_threshold_2 + 10]} ({var_esm.iloc[time_threshold_2 + 10]}) state<br>"
                    f"- and the signal {Signals.Columns.USER_INF} is in {signals['status_user_inf'].iloc[time_threshold_2 + 10]} ({user_inf.iloc[time_threshold_2 + 10]}) state<br><br>"
                    f"This confirms that AUPCore received the information that the front camera vision was unreliable and then it went into error <br>"
                    f"state and the AUPCore provided information about the reason of the error.".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                delay_neg_core = core_state.iloc[time_threshold_2 - 10] == aup.CORE_STATUS.CORE_ERROR
                delay_neg_esm = var_esm.iloc[time_threshold_2 - 10] != aup.ESM_STATE.ESM_NO_ERROR

                delay_pos_core = core_state.iloc[time_threshold_2 + 10] != aup.CORE_STATUS.CORE_ERROR
                delay_pos_esm = var_esm.iloc[time_threshold_2 + 10] != aup.ESM_STATE.ESM_IRREVERSIBLE_ERROR
                delay_pos_user = user_inf.iloc[time_threshold_2 + 10] != aup.HMI_MESSAGE.FRONT_CAM_VISION_UNRELIABLE

                if delay_neg_core or delay_neg_esm or delay_pos_core or delay_pos_esm or delay_pos_user:
                    if delay_neg_core and delay_neg_esm and delay_pos_core and delay_pos_esm and delay_pos_user:
                        timeline = "before and after"
                        reason = " ".join(
                            f"AUPCore wasn't error free before front camera vision was detected unreliable and it didn't transition to error state<br>"
                            f"- At time <b>{round(time.iloc[time_threshold_2 - 10], 3)}s {Signals.Columns.CORE_STATE} was in "
                            f"{signals['status_core_state'].iloc[time_threshold_2 - 10]} ({core_state.iloc[time_threshold_2 - 10]}) state "
                            f"- At time <b>{round(time.iloc[time_threshold_2 - 10], 3)}s {Signals.Columns.VAR_ESM } was in "
                            f"{signals['status_var_esm'].iloc[time_threshold_2 - 10]} ({var_esm.iloc[time_threshold_2 - 10]}) state "
                            f"- At time <b>{round(time.iloc[time_threshold_2 + 10], 3)}s {Signals.Columns.CORE_STATE} was in "
                            f"{signals['status_core_state'].iloc[time_threshold_2 + 10]} ({core_state.iloc[time_threshold_2 + 10]}) state "
                            f"- At time <b>{round(time.iloc[time_threshold_2 + 10], 3)}s {Signals.Columns.VAR_ESM } was in "
                            f"{signals['status_var_esm'].iloc[time_threshold_2 + 10]} ({var_esm.iloc[time_threshold_2 + 10]}) state"
                            f"- At time <b>{round(time.iloc[time_threshold_2 + 10], 3)}s {Signals.Columns.USER_INF} was in "
                            f"{signals['status_user_inf'].iloc[time_threshold_2 + 10]} ({user_inf.iloc[time_threshold_2 + 10]}) state".split()
                        )
                        if delay_neg_core or delay_neg_esm:
                            timeline = "before"
                            reason = " ".join(
                                f"AUPCore wasn't error free before front camera vision was detected unreliable.<br>"
                                f"- At time <b>{round(time.iloc[time_threshold_2 - 10], 3)}s {Signals.Columns.CORE_STATE} was in "
                                f"{signals['status_core_state'].iloc[time_threshold_2 - 10]} ({core_state.iloc[time_threshold_2 - 10]}) state "
                                f"- At time <b>{round(time.iloc[time_threshold_2 - 10], 3)}s {Signals.Columns.VAR_ESM } was in "
                                f"{signals['status_var_esm'].iloc[time_threshold_2 - 10]} ({var_esm.iloc[time_threshold_2 - 10]}) state".split()
                            )
                        elif delay_pos_core or delay_pos_esm or delay_pos_user:
                            timeline = "after"
                            reason = " ".join(
                                f"AUPCore didn't transition to error state due to front camera vision unreliable.<br>"
                                f"- At time <b>{round(time.iloc[time_threshold_2 +  10], 3)}s {Signals.Columns.CORE_STATE} was in "
                                f"{signals['status_core_state'].iloc[time_threshold_2 + 10]} ({core_state.iloc[time_threshold_2 + 10]}) state "
                                f"- At time <b>{round(time.iloc[time_threshold_2 +  10], 3)}s {Signals.Columns.VAR_ESM } was in "
                                f"{signals['status_var_esm'].iloc[time_threshold_2 + 10]} ({var_esm.iloc[time_threshold_2 + 10]}) state"
                                f"- At time <b>{round(time.iloc[time_threshold_2 +  10], 3)}s {Signals.Columns.USER_INF} was in "
                                f"{signals['status_user_inf'].iloc[time_threshold_2 + 10]} ({user_inf.iloc[time_threshold_2 + 10]}) state".split()
                            )
                        evaluation_1 = " ".join(
                            f"The evaluation FAILED {timeline} the moment <b>{round(time.iloc[time_threshold_2], 3)}s</b> "
                            f"when {Signals.Columns.FRONT_CAM} == 1. This means {reason}".split()
                        )
                        eval_cond_1 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.FRONT_CAM} == 1 was never found.".split()
                )
            if time_threshold_2 is not None and time_threshold_3 is not None and time_threshold_4 is not None:
                evaluation_2 = " ".join(
                    f"The evaluation is PASSED between the interval given by the signal {Signals.Columns.FRONT_CAM} == 1 "
                    f"and right before the signal {Signals.Columns.IGN_ON} == Ignition OFF (0) "
                    f"<b>({round(time.iloc[time_threshold_2], 3)} - {round(time.iloc[time_threshold_4 - 10], 3)})</b>, "
                    f"because the signal<br> {Signals.Columns.CORE_STATE} is in CORE_ERROR (5) state for the whole time, as expected."
                    f"<br><br>This confirms that the AUPcore remained in error state when ignition still on, even if the error dissapeard.".split()
                )
                eval_cond_2 = True  # set the evaluation condition as TRUE
                core_state_interval = core_state.iloc[(time_threshold_2 + 10) : (time_threshold_4 - 10)]
                error_state = front_cam.iloc[time_threshold_3 : (time_threshold_4 - 10)]
                cond_neg_core = (core_state_interval != aup.CORE_STATUS.CORE_ERROR).any()
                cond_neg_error = (error_state != 0).any()

                if cond_neg_core or cond_neg_error:
                    if cond_neg_core and cond_neg_error:
                        evaluation_2 = " ".join(
                            f"The evaluation FAILED between the interval given by the signal {Signals.Columns.FRONT_CAM} == 1<br> "
                            f"and right before the signal {Signals.Columns.IGN_ON} == Ignition OFF (0) "
                            f"<b>({round(time.iloc[time_threshold_2], 3)} - {round(time.iloc[time_threshold_5 - 10], 3)})s</b>,<br> "
                            f"because the signal {Signals.Columns.CORE_STATE} wasn't in CORE_ERROR (5) state for the whole time.<br><br>"
                            f"This means that AUPcore didn't remain in error state when ignition was still on and the error dissapeard.".split()
                        )
                    elif cond_neg_error:
                        evaluation_2 = " ".join(
                            f"The evaluation FAILED between the interval given by the signal {Signals.Columns.FRONT_CAM} == 1<br> "
                            f"and right before the signal {Signals.Columns.IGN_ON} == Ignition OFF (0) "
                            f"<b>({round(time.iloc[time_threshold_2], 3)} - {round(time.iloc[time_threshold_5 - 10], 3)})s</b>,<br> "
                            f"because the signal {Signals.Columns.FRONT_CAM} wasn't set to 0.<br><br>"
                            f"This means that the error wasn't eliminated, therefore it's not possible to check if AUPCore remains in error state<br>\
                                if error dissapears, but ignition is still on .".split()
                        )
                    eval_cond_2 = False
            elif time_threshold_3 is None:
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.FRONT_CAM} == 0 was never found between T2 and T4.<br>"
                    f"Therefore it's not possible to check if AUPCore remains in error state if error dissapears.".split()
                )
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_2 = " ".join(
                    f"Evaluation not possible, the trigger values {Signals.Columns.FRONT_CAM} == 1 or {Signals.Columns.IGN_ON} == Ignition OFF (0) "
                    f"were never found.".split()
                )

            if time_threshold_5 is not None:
                evaluation_3 = " ".join(
                    f"The evaluation is PASSED at moment <b>({round(time.iloc[time_threshold_2], 3)}s</b> when an ignition cycle is completed "
                    f"because the signal {Signals.Columns.CORE_STATE} is in CORE_INIT (0), as expected."
                    f"This confirms that the irreversible error is no longer seen by the AUPCore after an ignition cycle".split()
                )
                eval_cond_3 = True  # set the evaluation condition as TRUE

                delay_pos_core_init = core_state.iloc[time_threshold_5 + 10] != aup.CORE_STATUS.CORE_INIT

                if delay_pos_core_init:
                    evaluation_3 = " ".join(
                        f"The evaluation is FAILED at moment <b>{round(time.iloc[time_threshold_2], 3)}</b> when an ignition cycle is completed "
                        f"because the signal {Signals.Columns.CORE_STATE}<br> is in {signals['status_core_state'].iloc[time_threshold_5 + 10]} "
                        f"({core_state.iloc[time_threshold_5 + 10]}) state."
                        f"<br><br>This means that the irreversible error was still seen by the AUPCore after an ignition cycle.".split()
                    )
                    eval_cond_3 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_3 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.IGN_ON} == Ignition ON (1) "
                    f"was never found.".split()
                )

            if eval_cond_1 and eval_cond_2 and eval_cond_3:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            verdict2 = "PASSED" if eval_cond_2 else "FAILED" if eval_cond_2 is False else "NOT ASSESSED"
            verdict3 = "PASSED" if eval_cond_3 else "FAILED" if eval_cond_3 is False else "NOT ASSESSED"

            expected_val_1 = """delay -0.1s:<br>\
            AP.PARKSMCoreStatusPort.parksmCoreState_nu != CORE_ERROR (5)<br>\
            AP.psmDebugPort.stateVarESM_nu == ESM_NO_ERROR (1)<br>\
            delay 0.1s:<br>\
            AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_ERROR (5)<br>\
            AP.psmDebugPort.stateVarESM_nu == ESM_IRREVERSIBLE_ERROR (3)<br>\
            AP.apUserInformationPort.generalUserInformation_nu == FRONT_CAM_VISION_UNRELIABLE (43)<br>"""
            expected_val_2 = """delay -0.1: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_ERROR (5)"""
            expected_val_3 = """delay 0.1: AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_INIT (0)"""

            # you have to correlate the signal with the evaluation text in the table
            signal_summary["T2"] = [expected_val_1, evaluation_1, verdict1]
            signal_summary["T2 - T4"] = [expected_val_2, evaluation_2, verdict2]
            signal_summary["T5"] = [expected_val_3, evaluation_3, verdict3]

            remark = html_remark
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=front_cam,
                    mode="lines",
                    name=Signals.Columns.FRONT_CAM,
                    hovertemplate="Time: %{x}<br>Value: %{y}<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=ign_on,
                    mode="lines",
                    name=Signals.Columns.IGN_ON,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_ign_on"],
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
                    y=var_esm,
                    mode="lines",
                    name=Signals.Columns.VAR_ESM,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_var_esm"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=user_inf,
                    mode="lines",
                    visible="legendonly",
                    name=Signals.Columns.USER_INF,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_user_inf"],
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
            if time_threshold_3 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_3],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T3",
                )
            if time_threshold_4 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_4],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T4",
                )
            if time_threshold_5 is not None:
                fig.add_vline(
                    x=time.iat[time_threshold_5],
                    line_width=1,
                    line_dash="dash",
                    line_color="darkslategray",
                    annotation_text="T5",
                )
            if time_threshold_2 is not None and time_threshold_4 is not None:
                fig.add_vrect(
                    x0=time.iat[time_threshold_2],
                    x1=time.iat[time_threshold_4],
                    fillcolor="LimeGreen",
                    line_width=0,
                    opacity=0.3,
                    layer="below",
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
    name="SWRT_CNC_AUP_ManeuveringState_Table_51_Req_2325842_2325994_2325843",
    description=(
        "This test case verifies that if AUPCore receives the information that the front camera vision is unreliable, which is \
            an irreversible error, AUPCore shall go into error state and stay in this state until the ignition is switched off.\
                Also, information about the reason of the error shall be provided by AUPCore."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_51_Req_2325842_2325994_2325843_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_51_Req_2325842_2325994_2325843_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br>
                T1: start_of_measurement <br>
                T2: //front camera becomes unreliable<br>
                    <em>SignalManipulation.healthVector_frontCamVisionUnreliable</em> == 1 <br>
                T3: //heal condition<br>
                    <em>SignalManipulation.healthVector_frontCamVisionUnreliable</em> == 0 <br>
                T4: //turn off the engine<br>
                    <em>SignalManipulation.additionalBCMStatusPort_ignitionOn_nu</em> == 0 <br>
                T5: //turn in the engine<br>
                    <em>SignalManipulation.additionalBCMStatusPort_ignitionOn_nu</em> == 1 <br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T2: <br>
                delay -0.1s: //before the error condition, the system had no errors<br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> != CORE_ERROR (5) <br>
                    <em>AP.psmDebugPort.stateVarESM_nu</em> == ESM_NO_ERROR (1) <br>
                delay 0.1s: <br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_ERROR (5) <br>
                    <em>AP.psmDebugPort.stateVarESM_nu</em> == ESM_IRREVERSIBLE_ERROR (1) <br>
                    <em>AP.apUserInformationPort.generalUserInformation_nu</em> == FRONT_CAM_VISION_UNRELIABLE (43) <br>
                T2 - T4:<br>
                delay -0.1: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_ERROR (5) <br>
                T5:
                delay 0.1: <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_INIT (0) <br>


            </td>
        </tr>
    </table>

"""
