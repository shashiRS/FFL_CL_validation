"""
T1:
start_of_measurement

T2:
"SignalManipulation.healthVector_frontCamBlockage" = 1

ET2:
delay -0.1s:
"AP.PARKSMCoreStatusPort.parksmCoreState_nu" != {CORE_ERROR } (5)
"AP.CtrlCommandPort.emergencyBrake_nu" != 1
"AP.trajCtrlRequestPort.emergencyBrakeRequest" != 1
"AP.trajCtrlRequestPort.drivingModeReq_nu" != {MAKE_SECURE } (3)
"AP.psmDebugPort.stateVarESM_nu" == {ESM_NO_ERROR } (1)

delay 0.1s:
"AP.PARKSMCoreStatusPort.parksmCoreState_nu" == {CORE_ERROR } (5)
"AP.CtrlCommandPort.emergencyBrake_nu" == 1
"AP.trajCtrlRequestPort.emergencyBrakeRequest" == 1
"AP.trajCtrlRequestPort.drivingModeReq_nu" == {MAKE_SECURE } (3)
"AP.psmDebugPort.stateVarESM_nu" == {ESM_REVERSIBLE_ERROR } (2)
"AP.apUserInformationPort.generalUserInformation_nu" == {FRONT_CAM_BLOCKAGE} (87)
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
__copyfront__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "SWRT_CNC_AUP_ManeuveringState_Table_48_Req_2325840_2326038_2325843"


class Signals(SignalDefinition):
    """Signal definition."""

    # in this class you can define the signals which you will need for test
    # and which would be extracted from measurement

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        CAM_BLOCK = "SignalManipulation.healthVector_frontCamBlockage"
        CORE_STATE = "AP.PARKSMCoreStatusPort.parksmCoreState_nu"
        EM_BRAKE = "AP.CtrlCommandPort.emergencyBrake_nu"
        EM_BRAKE_REQ = "AP.trajCtrlRequestPort.emergencyBrakeRequest"
        DRV_MODE_REQ = "AP.trajCtrlRequestPort.drivingModeReq_nu"
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
            self.Columns.CAM_BLOCK: [
                "SignalManipulation.healthVector_frontCamBlockage",
            ],
            self.Columns.CORE_STATE: [
                "AP.PARKSMCoreStatusPort.parksmCoreState_nu",
            ],
            self.Columns.EM_BRAKE: [
                "AP.CtrlCommandPort.emergencyBrake_nu",
            ],
            self.Columns.EM_BRAKE_REQ: [
                "AP.trajCtrlRequestPort.emergencyBrakeRequest",
            ],
            self.Columns.DRV_MODE_REQ: [
                "AP.trajCtrlRequestPort.drivingModeReq_nu",
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
    name="Maneuvering State Table 48 Req 2325840 2326038 2325843",
    description=(
        "This test case verifies that if AUPCore receives the information that the front camera is blocked while  \
            in maneuvering state, it shall go into error state and the ego vehicle shall become standstill and it \
                should be secured. Also, the AUPCore shall receive and provide an information about the reason of the error."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(ALIAS, Signals)
class SWRT_CNC_AUP_ManeuveringState_Table_48_Req_2325840_2326038_2325843_TS(TestStep):
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
            cam_block = signals[Signals.Columns.CAM_BLOCK]
            core_state = signals[Signals.Columns.CORE_STATE]
            em_brake = signals[Signals.Columns.EM_BRAKE]
            em_brake_req = signals[Signals.Columns.EM_BRAKE_REQ]
            drv_mode_req = signals[Signals.Columns.DRV_MODE_REQ]
            var_esm = signals[Signals.Columns.VAR_ESM]
            user_inf = signals[Signals.Columns.USER_INF]

            signals["status_core_state"] = core_state.apply(lambda x: fh.get_status_label(x, aup.CORE_STATUS))
            signals["status_drv_mode_req"] = drv_mode_req.apply(lambda x: fh.get_status_label(x, aup.DRIVING_MODE))
            signals["status_var_esm"] = var_esm.apply(lambda x: fh.get_status_label(x, aup.ESM_STATE))
            signals["status_user_inf"] = user_inf.apply(lambda x: fh.get_status_label(x, aup.HMI_MESSAGE))

            def find_time_threshold(signal, state):
                trigger = signal == state
                if np.any(trigger):
                    return np.argmax(trigger)
                return None

            time_threshold_2 = find_time_threshold(cam_block, 1)

            if time_threshold_2 is not None:
                evaluation_1 = " ".join(
                    f"The evaluation is PASSED because <b>before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when "
                    f"the signal <b>{Signals.Columns.CAM_BLOCK}</b> == 1: <br>"
                    f"- the signal {Signals.Columns.CORE_STATE} is NOT in CORE_ERROR (5) state<br>"
                    f"- and the signals {Signals.Columns.EM_BRAKE} and {Signals.Columns.EM_BRAKE_REQ} != 1<br>"
                    f"- and the signal {Signals.Columns.DRV_MODE_REQ} is NOT in MAKE_SECURE (3) state<br>"
                    f"- and the signal {Signals.Columns.VAR_ESM} is in ESM_NO_ERROR (1) state<br>"
                    f"AND <b>after</b> that timestamp:<br>"
                    f"- the signal {Signals.Columns.CORE_STATE} is in CORE_ERROR (5) state<br>"
                    f"- and the signals {Signals.Columns.EM_BRAKE} and {Signals.Columns.EM_BRAKE_REQ} != 1<br>"
                    f"- and the signal {Signals.Columns.DRV_MODE_REQ} is in MAKE_SECURE (3) state<br>"
                    f"- and the signal {Signals.Columns.VAR_ESM} is in ESM_REVERSIBLE_ERROR (2) state<br>"
                    f"- and the signal {Signals.Columns.USER_INF} is in FRONT_CAM_BLOCKAGE (87) state<br>"
                    f"This confirms that AUPCore received the information that the front camera is blocked while in maneuvering state and then <br>"
                    f"it went into error state, the ego vehicle became standstill and it was secured and the AUPCore provided an information<br>"
                    f" about the reason of the error, which was 'front camera blockage'.".split()
                )
                eval_cond_1 = True  # set the evaluation condition as TRUE
                delay_neg_core = core_state.iloc[time_threshold_2 - 10] == aup.CORE_STATUS.CORE_ERROR
                delay_neg_br = (em_brake.iloc[time_threshold_2 - 10] == 1) and (
                    em_brake_req.iloc[time_threshold_2 - 10] == 1
                )
                delay_neg_drv = drv_mode_req.iloc[time_threshold_2 - 10] == aup.DRIVING_MODE.MAKE_SECURE
                delay_neg_esm = var_esm.iloc[time_threshold_2 - 10] != aup.ESM_STATE.ESM_NO_ERROR

                delay_pos_core = core_state.iloc[time_threshold_2 + 10] != aup.CORE_STATUS.CORE_ERROR
                delay_pos_br = (em_brake.iloc[time_threshold_2 + 10] != 1) and (
                    em_brake_req.iloc[time_threshold_2 + 10] != 1
                )
                delay_pos_drv = drv_mode_req.iloc[time_threshold_2 + 10] != aup.DRIVING_MODE.MAKE_SECURE
                delay_pos_esm = var_esm.iloc[time_threshold_2 + 10] != aup.ESM_STATE.ESM_REVERSIBLE_ERROR
                delay_pos_user = user_inf.iloc[time_threshold_2 + 10] != aup.HMI_MESSAGE.FRONT_CAM_BLOCKAGE

                if (
                    delay_neg_core
                    or delay_neg_br
                    or delay_neg_drv
                    or delay_neg_esm
                    or delay_pos_core
                    or delay_pos_br
                    or delay_pos_drv
                    or delay_pos_esm
                    or delay_pos_user
                ):
                    reason = ""
                    if (
                        delay_neg_core
                        and delay_neg_br
                        and delay_neg_drv
                        and delay_neg_esm
                        and delay_pos_core
                        and delay_pos_br
                        and delay_pos_drv
                        and delay_pos_esm
                        and delay_pos_user
                    ):
                        reason = "because <b>before</b> AUPCore detected the front camera blockage, AUPCore was already in error, the vehicle was stopped and secured<br>\
                            and <b>after</b> that the information about the error reason was not provided, the vehicle wasn't stopped and secured and AUPCore\
                                wasn't in error state. "
                    elif delay_neg_core or delay_neg_esm:
                        reason = " because <b>before</b> AUPCore detected the front camera blockage, AUPCore wasn't error free."
                    elif delay_neg_br:
                        reason = " because <b>before</b> AUPCore detected the front camera blockage the vehicle was standstill."
                    elif delay_neg_drv:
                        reason = (
                            " because <b>before</b> AUPCore detected the front camera blockage the vehicle was secured."
                        )
                    elif delay_pos_core or delay_pos_esm:
                        reason = " because <b>after</b> AUPCore detected the front camera blockage, AUPCore didn't transition to error state."
                    elif delay_pos_br:
                        reason = " because <b>after</b> AUPCore detected the front camera blockage the vehicle didn't go standstill."
                    elif delay_pos_drv:
                        reason = " because <b>after</b> AUPCore detected the front camera blockage the vehicle wasn't secured."

                    evaluation_1 = " ".join(
                        f"This evaluation is FAILED{reason}<br>. Evaluated signals have the follwing values/states:<br>"
                        f"<b>Before</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when {Signals.Columns.CAM_BLOCK} == 1:<br>"
                        f"- the signal {Signals.Columns.CORE_STATE} == {core_state.iloc[time_threshold_2 - 10]}<br>"
                        f"- the signal {Signals.Columns.EM_BRAKE} == {em_brake.iloc[time_threshold_2 - 10]}<br>"
                        f"- the signal {Signals.Columns.EM_BRAKE_REQ} == {em_brake_req.iloc[time_threshold_2 - 10]}<br>"
                        f"- the signal {Signals.Columns.DRV_MODE_REQ} == {drv_mode_req.iloc[time_threshold_2 - 10]}<br>"
                        f"- the signal {Signals.Columns.VAR_ESM} == {var_esm.iloc[time_threshold_2 - 10]}<br>"
                        f"- the signal {Signals.Columns.DRV_MODE_REQ} == {drv_mode_req.iloc[time_threshold_2 - 10]}<br>"
                        f"<b>After</b> the timestamp <b>{round(time.iloc[time_threshold_2], 3)}s</b> when {Signals.Columns.CAM_BLOCK} == 1:<br>"
                        f"- the signal {Signals.Columns.CORE_STATE} == {core_state.iloc[time_threshold_2 + 10]}<br>"
                        f"- the signal {Signals.Columns.EM_BRAKE} == {em_brake.iloc[time_threshold_2 + 10]}<br>"
                        f"- the signal {Signals.Columns.EM_BRAKE_REQ} == {em_brake_req.iloc[time_threshold_2 + 10]}<br>"
                        f"- the signal {Signals.Columns.DRV_MODE_REQ} == {drv_mode_req.iloc[time_threshold_2 + 10]}<br>"
                        f"- the signal {Signals.Columns.VAR_ESM} == {var_esm.iloc[time_threshold_2 + 10]}<br>"
                        f"- the signal {Signals.Columns.USER_INF} == {user_inf.iloc[time_threshold_2 + 10]}<br>".split()
                    )
                    eval_cond_1 = False
            else:
                # create an evaluation text for the moment when the threshold isn't found, set test_result to NOT_ASSESSED
                self.result.measured_result = FALSE
                evaluation_1 = " ".join(
                    f"Evaluation not possible, the trigger value {Signals.Columns.CAM_BLOCK} == 1 was never found.".split()
                )

            if eval_cond_1:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict1 = "PASSED" if eval_cond_1 else "FAILED" if eval_cond_1 is False else "NOT ASSESSED"
            expected_val_1 = """delay -0.1s:<br>
            AP.PARKSMCoreStatusPort.parksmCoreState_nu != CORE_ERROR (5)<br>\
            AP.CtrlCommandPort.emergencyBrake_nu != 1<br>\
            AP.trajCtrlRequestPort.emergencyBrakeRequest != 1<br>\
            AP.trajCtrlRequestPort.drivingModeReq_nu != MAKE_SECURE (3)<br>\
            AP.psmDebugPort.stateVarESM_nu == ESM_NO_ERROR (1)<br>\
            delay 0.1s:<br>\
            AP.PARKSMCoreStatusPort.parksmCoreState_nu == CORE_ERROR (5)<br>\
            AP.CtrlCommandPort.emergencyBrake_nu == 1<br>\
            AP.trajCtrlRequestPort.emergencyBrakeRequest == 1<br>\
            AP.trajCtrlRequestPort.drivingModeReq_nu == MAKE_SECURE (3)<br>\
            AP.psmDebugPort.stateVarESM_nu == ESM_REVERSIBLE_ERROR (2)<br>\
            AP.apUserInformationPort.generalUserInformation_nu == FRONT_CAM_BLOCKAGE (87)"""

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
                    y=cam_block,
                    mode="lines",
                    name=Signals.Columns.CAM_BLOCK,
                    hovertemplate="Time: %{x}<br>Value: %{y}<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=em_brake,
                    mode="lines",
                    name=Signals.Columns.EM_BRAKE,
                    hovertemplate="Time: %{x}<br>Value: %{y}<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=em_brake_req,
                    mode="lines",
                    name=Signals.Columns.EM_BRAKE_REQ,
                    hovertemplate="Time: %{x}<br>Value: %{y}<extra></extra>",
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
                    y=drv_mode_req,
                    mode="lines",
                    name=Signals.Columns.DRV_MODE_REQ,
                    hovertemplate="Time: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["status_drv_mode_req"],
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
    name="SWRT_CNC_AUP_ManeuveringState_Table_48_Req_2325840_2326038_2325843",
    description=(
        "This test case verifies that if AUPCore receives the information that the front camera is blocked while  \
            in maneuvering state, it shall go into error state and the ego vehicle shall become standstill and it \
                should be secured. Also, the AUPCore shall receive and provide an information about the reason of the error."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class SWRT_CNC_AUP_ManeuveringState_Table_48_Req_2325840_2326038_2325843_TC(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            SWRT_CNC_AUP_ManeuveringState_Table_48_Req_2325840_2326038_2325843_TS
        ]  # in this list all the needed test steps are included


html_remark = """

    <table>
        <tr>
            <td>
                <strong>Timeline Moments</strong><br>
                T1: start_of_measurement <br>
                T2: <br>
                    <em>SignalManipulation.healthVector_frontCamBlockage</em> == 1 <br><br>
            </td>
        </tr>
        <tr>
            <td>
                <strong>Timeframe of Evaluation</strong><br>
                T2: <br>
                delay -0.1s: <br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> != CORE_ERROR (5) <br>
                    <em>AP.CtrlCommandPort.emergencyBrake_nu</em> != 1 <br>
                    <em>AP.trajCtrlRequestPort.emergencyBrakeRequest</em> != 1 <br>
                    <em>AP.trajCtrlRequestPort.drivingModeReq_nu</em> != MAKE_SECURE (3) <br>
                    <em>AP.psmDebugPort.stateVarESM_nu</em> == ESM_NO_ERROR (1) <br>
                delay 0.1s: <br>
                    <em>AP.PARKSMCoreStatusPort.parksmCoreState_nu</em> == CORE_ERROR (5) <br>
                    <em>AP.CtrlCommandPort.emergencyBrake_nu</em> == 1 <br>
                    <em>AP.trajCtrlRequestPort.emergencyBrakeRequest</em> == 1 <br>
                    <em>AP.trajCtrlRequestPort.drivingModeReq_nu</em> == MAKE_SECURE (3) <br>
                    <em>AP.psmDebugPort.stateVarESM_nu</em> == ESM_REVERSIBLE_ERROR (2) <br>
                    <em>AP.apUserInformationPort.generalUserInformation_nu</em> == FRONT_CAM_BLOCKAGE (87) <br>
            </td>
        </tr>
    </table>

"""
