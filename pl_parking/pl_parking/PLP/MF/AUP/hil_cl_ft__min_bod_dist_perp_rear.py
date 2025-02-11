"""Body distance from high obstacle at final parking pose"""

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

SIGNAL_DATA = "BODY DISTANCE HIGH OBSTACLE PERPENDICULAR REAR SIDE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USER_ACTION = "HMI_action"
        CAR_SROAD = "Car_sroad"
        OBJ_SROAD = "Obj_sroad"
        CAR_TROAD = "Car_troad"
        OBJ_TROAD = "Obj_troad"
        PARKING_CORE_STATE = "Parking_core_state"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USER_ACTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut1.APHMIOutUserActionHU",
            self.Columns.CAR_TROAD: "CM.Vhcl.tRoad",
            self.Columns.OBJ_TROAD: "CM.Traffic.T00.tRoad",
            self.Columns.CAR_SROAD: "CM.Vhcl.sRoad",
            self.Columns.OBJ_SROAD: "CM.Traffic.T00.sRoad",
            self.Columns.PARKING_CORE_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Minimum body distance from high object",
    description="Body distance from high obstacle at final parking pose perpendicular rear side.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupAPMinBodDistPerpRearCheck(TestStep):
    """AupAPMinBodDistPerpRearCheck Test Step."""

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

        """Prepare signals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        ego_y = read_data["Car_troad"].tolist()
        object_y = read_data["Obj_troad"].tolist()
        state_on_hmi_sig = read_data["Parking_core_state"].tolist()
        hmi_action_sig = read_data["HMI_action"].tolist()

        t_success_idx = None
        t_start_idx = None

        evaluation1 = ""

        """Evaluation part"""
        # Find when parking core switches to automated park mode
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.Command.TOGGLE_AP_ACTIVE:
                t_start_idx = cnt
                break

        # Find when the driver terminated the maneuver via HMI
        for cnt in range(t_start_idx or 0, len(hmi_action_sig)):
            if hmi_action_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                t_success_idx = cnt
                break

        # If every t_#_idx is not None then every required condition fulfilled in a correct order
        if t_start_idx and t_success_idx:
            ego_pos = ego_y[t_success_idx]
            obj_pos = object_y[t_success_idx]
            if ego_pos - obj_pos > constants.ConstantsAUPBodyDistFinalPose.AP_G_DIST_MIN_SSIDE_HIGH_OBST_M:
                test_result = fc.PASS
                evaluation1 = " ".join(
                    "The test for checking minimal body distance between rear side and high object for perpendicular parking is PASSED.".split()
                )
            else:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f"The test for checking minimal body distance between rear side and high object for perpendicular parking is FAILED. The final parking pose was too close to the high object, it was"
                    f"{obj_pos-ego_pos} m while the maximum allowed is {constants.ConstantsAUPBodyDistFinalPose.AP_G_DIST_MIN_SSIDE_HIGH_OBST_M}".split()
                )

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                "The test for checking minimal body distance between rear side and high object for perpendicular parking is FAILED.".split()
            )

        if t_start_idx is None:
            evaluation1 += " ".join("The system did not start the automated parking maneuver.".split())
        if t_success_idx is None:
            evaluation1 += " ".join("The system did not finish the automated parking maneuver".split())

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Body distance from high obstacle at final parking pose"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["Parking_core_state"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=hmi_action_sig, mode="lines", name=signal_name["HMI_action"]))
            fig.add_trace(go.Scatter(x=time_signal, y=object_y, mode="lines", name=signal_name["Obj_troad"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ego_y, mode="lines", name=signal_name["Car_troad"]))

            fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
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
    name="Minimum body distance from high object perpendicular rear",
    description="Body distance from high obstacle at final parking pose perpendicular rear side.",
)
class AupAPMinBodDistPerpRear(TestCase):
    """AupAPMinBodDistPerpRear Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupAPMinBodDistPerpRearCheck,
        ]
