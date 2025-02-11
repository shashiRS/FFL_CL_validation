"""Vehicle state deactivation conditions, Tank cap"""

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

SIGNAL_DATA = "VEH_DEACT_TUNK_CAP"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        DRIVING_DIR = "Driv_dir"
        TUNK_CAP_STATE = "Tunk_cap_state"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.TUNK_CAP_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.TankCapOpen",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Tank cap state check",
    description="Check system reaction if tank cap set to OPEN during a parking maneuver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupVehDeactTankCapCheck(TestStep):
    """AupVehDeactTankCapCheck Test Step."""

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
        state_on_hmi_sig = read_data["State_on_HMI"].tolist()
        driving_dir_sig = read_data["Driv_dir"].tolist()
        tunk_cap_sig = read_data["Tunk_cap_state"].tolist()

        t_maneuver_idx = None  # Begining of parking maneuver
        t_tunk_open_idx = None  # Time point of tunk cap open
        t_limit_idx = None  # Standstill

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Driv_dir']} signal is PASSED, signal switches to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})"
            f" in {constants.HilCl.ApThreshold.TRESHOLD_TO_STANDSTILL} seconds after {signal_name['Tunk_cap_state']} signal switched to OPEN ({constants.HilCl.TunkCap.OPEN}).".split()
        )

        """Evaluation part"""

        # Find when AP switches to Maneuvering
        for cnt in range(0, len(state_on_hmi_sig)):
            if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_maneuver_idx = cnt
                break

        if t_maneuver_idx is not None:
            # Find when tunk cap open
            for cnt in range(t_maneuver_idx, len(tunk_cap_sig)):
                if tunk_cap_sig[cnt] == constants.HilCl.TunkCap.OPEN:
                    t_tunk_open_idx = cnt
                    break

            if t_tunk_open_idx is not None:
                # Find standstill
                for cnt in range(t_tunk_open_idx, len(driving_dir_sig)):
                    if driving_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                        t_limit_idx = cnt
                        break

                if t_limit_idx is not None:
                    # Set treshold to us
                    treshold_in_us = constants.HilCl.ApThreshold.TRESHOLD_TO_STANDSTILL * 1e6

                    # Calculate time to stop from event
                    delta_time = time_signal[t_limit_idx] - time_signal[t_tunk_open_idx]

                    # Compare with treshold
                    if delta_time < treshold_in_us:
                        eval_cond = [True] * 1
                        # Test Passed

                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal switches to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})"
                            f" after {signal_name['Tunk_cap_state']} signal switched to OPEN ({constants.HilCl.TunkCap.OPEN})"
                            f" but delta time between connection and standstill is {delta_time} us and treshold is {treshold_in_us} us.".split()
                        )

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal does not switch to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})"
                        f" after {signal_name['Tunk_cap_state']} signal switched to OPEN ({constants.HilCl.TunkCap.OPEN}).".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Tunk_cap_state']} signal is FAILED, signal never switched to OPEN ({constants.HilCl.TunkCap.OPEN})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to Maneuvering ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}) mode."
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

        signal_summary["Vehicle state deactivation, Set tank cap open during active parking maneuver"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=tunk_cap_sig, mode="lines", name=signal_name["Tunk_cap_state"]))
            fig.add_trace(go.Scatter(x=time_signal, y=driving_dir_sig, mode="lines", name=signal_name["Driv_dir"]))

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
    name="Vehicle state deactivation, Tunk cap open",
    description="The AP function shall have a vehicle state deactivation if the fuel tank cap is opened",
)
class AupVehDeactTankCap(TestCase):
    """AupVehDeactTankCap Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupVehDeactTankCapCheck,
        ]
