"""Check dynamic object classification cart."""

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

SIGNAL_DATA = "DYNAMIC_OBJECT_CLASSIFICATION_CART"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        CAR_SPEED = "Car_speed"
        DRIVING_DIR = "Driv_dir"
        DYNAMIC_OBJ_POS_LAT = "Dynamic_obj_position_lat"
        DYNAMIC_OBJ_POS_LONG = "Dynamic_obj_position_long"
        CAR_HITCH_X = "Car_hitch_x"
        HMI_INFO = "State_on_HMI"
        EMEGENCY_HOLD_REQ = "Emergency_hold_request"
        USER_ACTION = "User_action"
        EGO_LONG_ACCEL = "ego_long_accel"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.EMEGENCY_HOLD_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.DYNAMIC_OBJ_POS_LONG: "CM.Traffic.T00.tx",
            self.Columns.DYNAMIC_OBJ_POS_LAT: "CM.Traffic.T00.ty",
            self.Columns.CAR_SPEED: "CM.Car.vx",
            self.Columns.CAR_HITCH_X: "Car.Hitch.tx",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.EGO_LONG_ACCEL: "CM.Car.ax",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Object classification",
    description="Check dynamic object classification - cart",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class DynamicObjCheckCart(TestStep):
    """DynamicObjCheckCart Test Step."""

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
        time_sig = read_data.index
        car_speed_sig = read_data["Car_speed"].tolist()
        car_hitch_x = read_data["Car_hitch_x"].tolist()
        user_act_sig = read_data["User_action"].tolist()
        driv_dir_sig = read_data["Driv_dir"].tolist()
        em_hold_req_sig = read_data["Emergency_hold_request"].tolist()
        dynamic_obj_pos_lat = read_data["Dynamic_obj_position_lat"].tolist()
        dynamic_obj_pos_long = read_data["Dynamic_obj_position_long"].tolist()

        t1_idx = None
        t2_idx = None
        t3_idx = None

        def distance_ego_target(t_idx):

            #Get the pos for front ego veh
            ego_stopped = car_hitch_x[t_idx] + constants.ConstantsSlotDetection.CAR_LENGTH

            #Get the target pos
            target_pos = dynamic_obj_pos_long[t_idx] - (constants.HilCl.CarMaker.PEDESTRIAN_FEMALE_SENIOR_02_BABYSTROLLER_WIDTH / 2)

            # Calculate the distance
            distance_ego_target = round(target_pos - ego_stopped, 3)

            return distance_ego_target

        """Evaluation part"""
        # Find when user activate the AP function
        for idx, item in enumerate(user_act_sig):
            if item == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t1_idx = idx
                break

        if t1_idx is not None:
            # Find emergency hold request
            for cnt in range(t1_idx, len(em_hold_req_sig)):
                if em_hold_req_sig[cnt] == constants.HilCl.LoDMCEmergencyHoldRequest.TRUE:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                # Find when ego vehicle is in standtill
                for cnt in range(t2_idx, len(driv_dir_sig)):
                    if driv_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                        t3_idx = cnt
                        break

                if t3_idx is not None:
                    eval_cond = [True] * 1

                    caulculate_distance = distance_ego_target(t3_idx)

                    if caulculate_distance <= 0:
                        evaluation1 = " ".join(
                            f"The evaluation of ego position signal is FAILED, ego vehicle not stopped in time"
                            f" and the distace between ego vehicle and static object is {caulculate_distance} m.".split()
                        )
                    else:
                        evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Emergency_hold_request']} and {signal_name['Driv_dir']} signals are PASSED,"
                                f" {signal_name['Emergency_hold_request']} signal swithes to TRUE ({constants.HilCl.LoDMCHoldReq.TRUE}) and "
                                f" {signal_name['Driv_dir']} signal switches to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})."
                                f" Distance between front side of ego vehicle and static object is {caulculate_distance} m."
                                " Reaction of AP function is correct.".split()
                            )
                else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal never switched to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})."
                            " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                        )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Emergency_hold_request']} signal is FAILED, signal never switched to TRUE ({constants.HilCl.LoDMCHoldReq.TRUE})"
                    " There was no brake request as a reaction of AP function."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['User_action']} signal is FAILED, signal never switched to TOGGLE_AP_ACTIVE ({constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE}). AP funtion was never activated."
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

        signal_summary[
            "Check the reaction of the system if a target appears in fron of the ego vehicle"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_sig, y=car_speed_sig, mode="lines", name=signal_name["Car_speed"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.add_trace(go.Scatter(x=time_sig, y=car_hitch_x, mode="lines", name=signal_name["Car_hitch_x"]))
        fig.add_trace(go.Scatter(x=time_sig, y=em_hold_req_sig, mode="lines", name=signal_name["Emergency_hold_request"]))
        fig.add_trace(go.Scatter(x=time_sig, y=dynamic_obj_pos_lat, mode="lines", name=signal_name["Dynamic_obj_position_lat"]))
        fig.add_trace(go.Scatter(x=time_sig, y=dynamic_obj_pos_long, mode="lines", name=signal_name["Dynamic_obj_position_long"]))
        fig.add_trace(go.Scatter(x=time_sig, y=driv_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
        fig.add_trace(go.Scatter(x=time_sig, y=user_act_sig, mode="lines", name=signal_name["User_action"]))
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        """Calculate parameters to additional table"""
        sw_combatibility = (  # Remainder: Update if SW changed and script working well
            "swfw_apu_adc5-2.1.0-DR2-PLP-B1-PAR230"
        )

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            "Used SW version": {"value": sw_combatibility},
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
    name="Reaction on dynamic objects",
    description="The AP Function shall consider carts as dynamic objects",
)
class FtCommon(TestCase):
    """CommonDynamicObj Test Case."""

    custom_report = MfHilClCustomTestcaseReport
    # Important iformation:
    # Please use this script only with TestRun HIL_COMMON_DynamicTargetDetectionCartId1601952

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            DynamicObjCheckCart,
        ]
