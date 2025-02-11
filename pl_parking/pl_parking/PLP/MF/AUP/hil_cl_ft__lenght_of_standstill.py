"""Lenght if standstill in case of direction chacnhe"""

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

SIGNAL_DATA = "STANDSTILL_TIME"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        GEAR = "Gear"
        DRIV_DIR = "Driv_dir"
        REM_DEVICE_CONNECTED = "Rem_device_connected"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GEAR: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.DRIV_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.REM_DEVICE_CONNECTED: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIOut2.APHMIOutBTDevConnected",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Time of standstill between direction chacnge",
    description="Check waiting time in standstill in case of direction change",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class SotifStanstillTimeCheck(TestStep):
    """SotifStanstillTimeCheck Test Step."""

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
        gear_sig = read_data["Gear"].tolist()
        driv_dir_sig = read_data["Driv_dir"].tolist()
        rem_device_con_sig = read_data["Rem_device_connected"].tolist()

        t_maneuvering_start_idx = None
        t_maneuvering_end_idx = None
        time_limit = None

        rc_maneuver = False

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Driv_dir']} signal is PASSED,"
            " ego vehicle stays in standstill more the limit in case of all direction change during maneuvering.".split()
        )

        """Evaluation part"""
        # Find  Maneuvering
        for cnt, item in enumerate(state_on_hmi_sig):
            if (
                item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
                and t_maneuvering_start_idx is None
            ):
                t_maneuvering_start_idx = cnt
                continue
            if (
                item != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING
                and t_maneuvering_start_idx is not None
            ):
                t_maneuvering_end_idx = cnt
                break
        if t_maneuvering_start_idx is not None:

            if t_maneuvering_end_idx is not None:

                eval_cond = [True] * 1

                # Check RC or normal maneuver
                for item in enumerate(rem_device_con_sig):
                    if item == constants.HilCl.Hmi.BTDevConnected.TRUE:
                        rc_maneuver = True
                        break

                if rc_maneuver:
                    time_limit = constants.HilCl.SotifParameters.T_MOVE_RC
                else:
                    time_limit = constants.HilCl.SotifParameters.T_MOVE_VEHICLE

                # Collect gear shifts during maneuvering
                states_dict = HilClFuntions.States(gear_sig, t_maneuvering_start_idx, t_maneuvering_end_idx + 1, 1)

                # Keys contains the idx
                for key in states_dict:
                    for cnt in range(key, len(driv_dir_sig)):
                        if driv_dir_sig[cnt] != constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                            end_idx = cnt
                            break

                    delta = time_signal[end_idx] - time_signal[key]

                    if delta < time_limit * 1e6:
                        eval_cond[0] = False
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Driv_dir']} signal is FAILED,"
                            f" signal switches out form STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}) at {time_signal[end_idx]} us."
                            f" Time point of gear shift is at {time_signal[key]} us"
                            f" Time gap between gearshift and begining of vehicle moving is {round(delta * 1e-6, 3)} second(s)."
                            f" This is more then {time_limit} second(s)".split()
                        )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched out from PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
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
            f"Hold standstill position at least:"
            f"<br> - Normal parking: {constants.HilCl.SotifParameters.T_MOVE_VEHICLE} second(s) "
            f"<br> - Remote parking: {constants.HilCl.SotifParameters.T_MOVE_RC} second(s) "
            "<br> in case of forward/backward direction change during"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=gear_sig, mode="lines", name=signal_name["Gear"]))
            fig.add_trace(go.Scatter(x=time_signal, y=driv_dir_sig, mode="lines", name=signal_name["Driv_dir"]))

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
    name="Waiting time in standstill",
    description=f"The system shall wait in standstill position at least {constants.HilCl.SotifParameters.T_MOVE_VEHICLE} seconds in case of normal parking"
    f" and {constants.HilCl.SotifParameters.T_MOVE_RC} seconds in case of remote parking in case of forward/backward direction change during parking.",
)
class SotifStanstillTime(TestCase):
    """SotifStanstillTime Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SotifStanstillTimeCheck,
        ]
