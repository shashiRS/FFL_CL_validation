"""Acceleration limit check while maneuvering."""

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

SIGNAL_DATA = "SOTIF_ACCELERATION_LIMIT_CHECK"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        ACCELERATION = "Acceleration"
        HMI_INFO = "State_on_HMI"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ACCELERATION: "CM.Car.ax",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Acceleration check",
    description="Acceleration limit check while maneuvering.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupSotifAccTestCheck(TestStep):
    """AupSotifAccTestCheck Test Step."""

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
        acc_sig = read_data["Acceleration"].tolist()
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()

        t_getting_off_idx = None
        t_terminate_idx = None

        evaluation1 = ""

        """Evaluation part"""
        # Find when the AP start maneuvering
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_getting_off_idx = cnt
                break

        # Find when parking core performed the parking
        for cnt in range(t_getting_off_idx or 0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SUCCESS:
                t_terminate_idx = cnt
                break

        # If every t_#_idx is not None then every required condition fulfilled in a correct order
        if (
            t_getting_off_idx
            and t_terminate_idx
            and max(acc_sig[t_getting_off_idx:t_terminate_idx])
            <= constants.HilCl.ApThreshold.AP_G_MAX_AVG_LONG_ACCEL_MPS2
        ):
            test_result = fc.PASS
            evaluation1 = " ".join(
                f"The test for checking the system maximum allowed acceleration ({constants.HilCl.ApThreshold.AP_G_MAX_AVG_LONG_ACCEL_MPS2} m/s2) while parking is PASSED."
                f"The maximum acceleration during maneuvering was {max(acc_sig[t_getting_off_idx:t_terminate_idx])} m/s2 at "
                f"{acc_sig.index(max(acc_sig[t_getting_off_idx:t_terminate_idx]))} us.".split()
            )

        else:
            test_result = fc.FAIL
            evaluation1 = " ".join(
                f"The test for checking the system maximum allowed acceleration ({constants.HilCl.ApThreshold.AP_G_MAX_AVG_LONG_ACCEL_MPS2} m/s2) while parking is FAILED."
                f"The maximum acceleration during maneuvering was {max(acc_sig[t_getting_off_idx:t_terminate_idx])} m/s2 at "
                f"{acc_sig.index(max(acc_sig[t_getting_off_idx:t_terminate_idx]))} us.".split()
            )

        if t_getting_off_idx is None:
            evaluation1 += " ".join("The system did not transition to Getting off mode.".split())
        if max(acc_sig[t_getting_off_idx:t_terminate_idx]) > constants.HilCl.ApThreshold.AP_G_MAX_AVG_CTRL_V_MPS:
            evaluation1 += " ".join("The system exceeded the acceleration limit.".split())
        if t_terminate_idx is None:
            evaluation1 += " ".join("The system did not finish the maneuver.".split())

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Acceleration limit check while maneuvering"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=acc_sig, mode="lines", name=signal_name["Acceleration"]))

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
    name="Acceleration check",
    description="Acceleration limit check while maneuvering.",
)
class AupSotifAccTest(TestCase):
    """AupSotifAccTest Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupSotifAccTestCheck,
        ]
