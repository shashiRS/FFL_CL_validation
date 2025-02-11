"""React on statick object. System shall not brake"""

import logging
import os
import sys

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.mdf import MDFSignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import HilClFuntions, MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "NOT_BRAKE_ON_STATIC_OBJ"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USER_ACTION = "User_action"
        EMEGENCY_HOLD_REQ = "Emergency_hold_request"
        DRIVING_DIR = "Driv_dir"
        CAR_SROAD = "Car_sroad"
        OBJ_SROAD = "Obj_sroad"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.CAR_SROAD: "CM.Car.Road.sRoad",
            self.Columns.OBJ_SROAD: "CM.Traffic.T00.sRoad",
            self.Columns.EMEGENCY_HOLD_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="React on static object",
    description="Check AP function reaction on a static object.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonStaticNotBrakeOnCheck(TestStep):
    """CommonStaticNotBrakeOnCheck Test Step."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        """Init test."""
        super().__init__()

    def process(self, **kwargs):
        """
        This function processes the recorded signal from measurement file, set the result of the test,
        generate plots and additional results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        read_data = self.readers[SIGNAL_DATA]
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare sinals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        user_act_sig = read_data["User_action"].tolist()
        em_hold_req_sig = read_data["Emergency_hold_request"].tolist()
        driv_dir_sig = read_data["Driv_dir"].tolist()
        car_sroad_sig = read_data["Car_sroad"].tolist()
        obj_pos_sig = read_data["Obj_sroad"].tolist()

        t1_idx = None
        t2_idx = None

        """Evaluation part"""
        # Find when user activate the AP function
        for idx, item in enumerate(user_act_sig):
            if item == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t1_idx = idx
                break

        if t1_idx is not None:
            # Find when ego stops after AP activation
            for cnt in range(t1_idx, len(driv_dir_sig)):
                if driv_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                eval_cond = [True] * 1

                # Get sRoad of ego and object at t2_idx
                sroad_at_stop = car_sroad_sig[t2_idx]
                position_of_obj = obj_pos_sig[t2_idx]

                # Check emergency signal
                for cnt in range(t1_idx, t2_idx):
                    if em_hold_req_sig[cnt] == constants.HilCl.LoDMCEmergencyHoldRequest.TRUE:

                        eval_cond[0] = False
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Emergency_hold_request']} signal is FAILED,"
                            f" signal was TRUE ({constants.HilCl.LoDMCEmergencyHoldRequest.TRUE}) at {time_signal[cnt]} us"
                            " but system shall not activate brake in this case.".split()
                        )
                        break

                # Check ego position
                if sroad_at_stop > position_of_obj and eval_cond[0] is not False:
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Emergency_hold_request']} and {signal_name['Car_sroad']} signals are PASSED."
                        f" {signal_name['Emergency_hold_request']} signal never switched to TRUE ({constants.HilCl.LoDMCEmergencyHoldRequest.TRUE}) and"
                        f" distance traveled by ego vehicle ({sroad_at_stop} m) more than the position of traffic object ({position_of_obj} m).".split()
                    )

                if sroad_at_stop <= position_of_obj and eval_cond[0] is not False:
                    eval_cond[0] = False

                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Car_sroad']} signal is FAILED,"
                        f" distance traveled by ego vehicle ({sroad_at_stop} m) less than the position of traffic object ({position_of_obj} m)".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal never switched to STANDTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})"
                    f" after TOGGLE_AP_ACTIVE ({constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE}) event."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['User_action']} signal is FAILED, signal never switched to TOGGLE_AP_ACTIVE ({constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE})."
                " AP funtion was never activated."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        if all(eval_cond):
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["React on static object. System shall not brake on atatic object"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=em_hold_req_sig, mode="lines", name=signal_name["Emergency_hold_request"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=driv_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
            fig.add_trace(go.Scatter(x=time_signal, y=car_sroad_sig, mode="lines", name=signal_name["Car_sroad"]))
            fig.add_trace(go.Scatter(x=time_signal, y=obj_pos_sig, mode="lines", name=signal_name["Obj_sroad"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
            fig.update_layout(PlotlyTemplate.lgt_tmplt)

            plot_titles.append("")
            plots.append(fig)
            remarks.append("")

        """Calculate parameters to additional table"""

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
        }

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="Reaction on statick object",
    description="The AP function shall be able to react on static objects.",
)
class CommonStaticNotBrakeOn(TestCase):
    """CommonStaticNotBrakeOn Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonStaticNotBrakeOnCheck,
        ]
