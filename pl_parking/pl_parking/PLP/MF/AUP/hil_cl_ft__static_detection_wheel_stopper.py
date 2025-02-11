"""Check the behavior in case of static detection as wheel stopper."""

import logging
import math
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

SIGNAL_DATA = "HEIGHT_CLASSIFICATION_BODY_TRAV"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        STATIC_OBJ_POS = "Static_obj_position"
        CAR_HITCH_Y = "Car_hitch_y"
        HMI_INFO = "State_on_HMI"
        DRIVING_DIR = "Driv_dir"
        YAW_RATE = "Yaw_rate"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CAR_HITCH_Y: "Car.Hitch.ty",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.YAW_RATE: "CM.Vhcl.Yaw",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Static detection",
    description="Check wheel stopper as object classification",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class DetectionWheelStopper(TestStep):
    """DetectionWheelStopper Test Step."""

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
        car_hitch_y = read_data["Car_hitch_y"].tolist()
        HMI_Info = read_data["State_on_HMI"].tolist()
        driving_dir_sig = read_data["Driv_dir"].tolist()
        yaw_rate = read_data["Yaw_rate"].tolist()

        WHEEL_STOPPER_WIDTH = 0.2
        OBSTACLE_OFFSET = 1.5
        # wheel_stopper_position_y = 3 + 6 - 1.5 - 0.1
        wheel_stopper_position_y = constants.HilCl.CarMaker.LANE_WIDTH + constants.HilCl.CarMaker.PARKING_SLOT_WIDTH - OBSTACLE_OFFSET - ( WHEEL_STOPPER_WIDTH / 2 )

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            "The evaluation of static object detection is PASSED,"
            " ego veh park successfully park with the limits.".split()
        )

        """Evaluation part"""
        # Find the moment when AVG start to control ( ParkingProcedureCtrlState = PPC_PERFORM_PARKING)
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find the moment when AVG finish the parking ( ParkingProcedureCtrlState = PPC_SUCCESS) and ego car is in standstill
            for cnt in range(t1_idx, len(HMI_Info)):
                if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS and driving_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL :
                    t2_idx = cnt
                    break

            if t2_idx is not None:

                # alpha angle 90 degree - yaw rate
                alpha = abs(1.57079633 - yaw_rate[t2_idx])

                #1ST CASE WHERE THE PARKING SLOT IS ON THE RIGHT SIDE:

                # STARTING FROM THE POSITION OF THE HITCH, WE FORM A RIGHT-ANGLE TRIANGLE WITH THE REAR AXLE OF THE CAR
                # AND CALCULATE THE LONG LEG

                distance_to_rear_axle = constants.HilCl.CarMaker.OverhangPassatB8 * math.cos(alpha)

                # FROM THE REAR AXLE OF THE CAR, WE FORMA A RIGHT-ANGLE TRIANGLE WITH THE MIDDLE OF THE REAR WHEEL AXLE
                # AND CALCULATE THE SMALL LEG

                small_leg_wheel = ( constants.ConstantsSlotDetection.CAR_WIDTH / 2 ) * math.sin(alpha)

                # STARTING FROM THE CENTER OF THE WHEEL, WE FORM A RIGHT-ANGLED TRINGLE WITH THE REAR END OF THE WHEEL
                # AND CALCULATE THE LONG LEG

                long_leg_wheel = ( constants.ConstantsSlotDetection.WHEEL_DIAMETER / 2 ) * math.cos(alpha)

                # CALCULATE THE BACK END OF THE WHEEL POSITION Y

                back_end_wheel_y = car_hitch_y[t2_idx] + (-1) * (distance_to_rear_axle - small_leg_wheel - long_leg_wheel)

                """
                FOR THE SCENARIOS WHERE THE PARKING SLOT IS ON THE LEFT SIDE, THE DISTANCE CAN BE VERIFIED USING THE SAME LOGIC:

                * STARTING FROM THE POSITION OF THE HITCH, WE ARE CALCULATING THE DISTANCE TO THE REAR AXLE OF THE CAR

                distance_to_rear_axle = constants.HilCl.CarMaker.OverhangPassatB8 * math.cos(alpha)

                # FROM THE REAR AXLE OF THE CAR, WE FORMA A RIGHT-ANGLE TRIANGLE WITH THE MIDDLE OF THE REAR WHEEL AXLE
                # AND CALCULATE THE SMALL LEG

                small_leg_wheel = ( constants.ConstantsSlotDetection.CAR_WIDTH / 2 ) * math.sin(alpha)

                # STARTING FROM THE CENTER OF THE WHEEL, WE FORM A RIGHT-ANGLED TRINGLE WITH THE REAR END OF THE WHEEL
                # AND CALCULATE THE LONG LEG

                long_leg_wheel = ( constants.ConstantsSlotDetection.WHEEL_DIAMETER / 2 ) * math.cos(alpha)

                # CALCULATE THE BACK END OF THE WHEEL POSITION Y

                back_end_wheel_y = car_hitch_y[t2_idx] + (-1) * (distance_to_rear_axle - small_leg_wheel - long_leg_wheel)
                """

                if abs (back_end_wheel_y ) > abs(wheel_stopper_position_y):
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    "The evaluation of static object detection is FAILED,"
                    " ego vehicle goes beyond the wheel stopper.".split()
                    )
                elif abs (back_end_wheel_y) < abs(wheel_stopper_position_y) - constants.HilCl.ApThreshold.AP_G_MAX_DIST_WHEEL_STOPPER_M:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    "The evaluation of static object detection is FAILED,"
                    " the distance between the wheel and wheel stopper is larger than AP_G_MAX_DIST_WHEEL_STOPPER_M.".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    "The evaluation of static object detection is FAILED,"
                    " AVG didn't successfully park the ego car".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                "The evaluation of static object detection is FAILED,"
                " AVG never in control.".split()
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
            "Check the reaction of the system if a obstacle is present in the parking slot"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.add_trace(go.Scatter(x=time_sig, y=car_hitch_y, mode="lines", name=signal_name["Car_hitch_y"]))
        fig.add_trace(go.Scatter(x=time_sig, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_sig, y=driving_dir_sig , mode="lines", name=signal_name["Driv_dir"]))
        fig.add_trace(go.Scatter(x=time_sig, y=yaw_rate, mode="lines", name=signal_name["Yaw_rate"]))
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

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
    name="Static object classification: wheel stopper",
    description=f"The AP Function shall consider static objects higher than {constants.HilCl.HeightLimits.AP_G_MAX_HEIGHT_WHEEL_TRAVER_M}"
    f" m but lower or equal than {constants.HilCl.HeightLimits.AP_G_MAX_HEIGHT_BODY_TRAVER_M} m as wheel stopper and park within a max"
    f" distance equal with {constants.HilCl.ApThreshold.AP_G_MAX_DIST_WHEEL_STOPPER_M }m from at least one of the rear wheels to it .",
)
class FtCommon(TestCase):
    """CommonBodyTrav Test Case."""

    custom_report = MfHilClCustomTestcaseReport
    # Important iformation:
    # Please use this script only with TestRun DetectionWheelStopper

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            DetectionWheelStopper,
        ]
