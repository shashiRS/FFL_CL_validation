"""RC Outside Parking Out to Init, Vehicle state deactivation is triggered"""

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

SIGNAL_DATA = "RC_PARK_OUTTO_INIT_VEH_DEACT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        DOOR_STATE = "Door_state"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DOOR_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput01.DoorOpen",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name=" System reaction on door open event ",
    description="Check system reaction on door open event during RC Outside Parking Out state",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonRcGetOffToInitVehDeactCheck(TestStep):
    """CommonRcGetOffToInitVehDeactCheck Test Step."""

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
        door_sig = read_data["Door_state"].tolist()

        t_scanning_out_idx = None
        t_door_open_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, state of signal is PPC_INACTIVE ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE})"
            f" after door open event.".split()
        )

        """Evaluation part"""
        # Find begining of Scanning Out
        for cnt, item in enumerate(state_on_hmi_sig):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT:
                t_scanning_out_idx = cnt
                break

        if t_scanning_out_idx is not None:

            # Find when door set to open
            for cnt in range(t_scanning_out_idx, len(door_sig)):
                if door_sig[cnt] == constants.HilCl.Door.DOORSTATE_ENG_HOOD_OPEN:
                    t_door_open_idx = cnt
                    break

            if t_door_open_idx is not None:

                # Check signal states
                eval_cond = [True] * 1
                counter = 0

                # Collect states of AP after switch to Maneuvering event
                states_dict = HilClFuntions.States(state_on_hmi_sig, t_scanning_out_idx, len(state_on_hmi_sig), 1)

                # Keys contains the idx
                # Check mode after Maneuvering mode
                for key in states_dict:
                    if counter == 1:
                        actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                            states_dict[key]
                        )
                        actual_number = int(states_dict[key])

                        if key < t_door_open_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to {actual_value} ({actual_number}) at {time_signal[key]} us"
                                f" before door open event.".split()
                            )
                            eval_cond[0] = False
                            break

                        if states_dict[key] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, state of signal is {actual_value} ({actual_number}) at {time_signal[key]} us"
                                f" but requiered mode is PPC_INACTIVE ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_INACTIVE}).".split()
                            )
                            eval_cond[0] = False
                            break
                        counter += 1

                    else:
                        counter += 1

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Door_state']} signal is FAILED, signal never switched to DOORSTATE_ENG_HOOD_OPEN ({constants.HilCl.Door.DOORSTATE_ENG_HOOD_OPEN})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_SCANNING_OUT ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT})."
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

        signal_summary["Required state change: RC Outside Parking Out to Init. Reason: Vehicle deactivation"] = (
            evaluation1
        )

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=door_sig, mode="lines", name=signal_name["Door_state"]))

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
    name="Mode transition, RC Outside Parking Out to Init, Vehicle state deactivation is triggered",
    description="The function shall switch from RC Outside Parking Out to Init mode, if vehicle state deactivation is triggered.",
)
class CommonRcGetOffToInitVehDeact(TestCase):
    """CommonRcGetOffToInitVehDeact Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonRcGetOffToInitVehDeactCheck,
        ]
