"""Check the behavior in case of static detection as curbstone."""

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

SIGNAL_DATA = "STATIC_OBSTACLE_CURBSTONE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        CAR_TROAD = "Car_troad"
        HMI_INFO = "State_on_HMI"
        DRIVING_DIR = "Driv_dir"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CAR_TROAD: "CM.Vhcl.tRoad",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Static detection",
    description="Check Curbstone detection and behavior",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CurbstoneDetectionCheck(TestStep):
    """CurbstoneDetectionCheck Test Step."""

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
        car_troad = read_data["Car_troad"].tolist()
        HMI_Info = read_data["State_on_HMI"].tolist()
        driving_dir_sig = read_data["Driv_dir"].tolist()

        # initial lane widht + parking slot width which is ego width + 70cm
        curbstone_position = constants.HilCl.CarMaker.LANE_WIDTH + constants.ConstantsSlotDetection.CAR_WIDTH + 0.7

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            "The evaluation of static object detection is PASSED,"
            " ego veh park successfully park within the limits.".split()
        )

        """Evaluation part"""
        # Find the moment when AVG start the parking maneuver ( ParkingProcedureCtrlState = PPC_PERFORM_PARKING)
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find the moment when AVG successfully finish the parking maneuver ( ParkingProcedureCtrlState = PPC_SUCCESS) and the car is in standstill
            for cnt in range(t1_idx, len(HMI_Info)):
                if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS and driving_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL :
                    t2_idx = cnt
                    break

            if t2_idx is not None:

                dist_to_curbstone = curbstone_position - ( abs(car_troad[t2_idx]) + (constants.ConstantsSlotDetection.CAR_WIDTH / 2) )

                if dist_to_curbstone < constants.ConstantsAUPBodyDistFinalPose.AP_G_DIST_MIN_LSIDE_TRAV_PAR_M:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                    "The evaluation of static object detection is FAILED,"
                    " ego vehicle goes beyond the min distance.".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    "The evaluation of static object detection is FAILED,"
                    " AVG didn't successfully park the car".split()
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
            "Check the reaction of the system in case of a curbstone near the parking slot"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.add_trace(go.Scatter(x=time_sig, y=car_troad, mode="lines", name=signal_name["Car_troad"]))
        fig.add_trace(go.Scatter(x=time_sig, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_sig, y=driving_dir_sig , mode="lines", name=signal_name["Driv_dir"]))
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
    name="Static object detection: curbstone",
    description=f"The AP Function shall consider a curbstone if it is in the range [{constants.HilCl.HeightLimits.AP_G_MIN_HEIGHT_OBSTACLE_M}"
    f" , {constants.HilCl.HeightLimits.AP_G_MAX_HEIGHT_CURBSTONE_M}] m and park within a min"
    f" distance equal with {constants.ConstantsAUPBodyDistFinalPose.AP_G_DIST_MIN_LSIDE_TRAV_PAR_M }m to it.",
)
class CurbstoneDetection(TestCase):
    """CommonBodyTrav Test Case."""

    custom_report = MfHilClCustomTestcaseReport
    # Important iformation:
    # Please use this script only with TestRun CurbstoneDetection

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CurbstoneDetectionCheck,
        ]
