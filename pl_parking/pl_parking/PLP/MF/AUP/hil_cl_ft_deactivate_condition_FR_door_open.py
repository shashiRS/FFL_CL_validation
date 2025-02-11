"""The goal of this TC is to validate the system behavior in case the front right door is open during maneuvering state."""
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

__author__ = "VALERICA ATUDOSIEI"

SIGNAL_DATA = "MANEUVERING_TO_INIT_DOOR_OPEN_FR"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        DOOR_STATE = "Door_state"
        DRIVING_DIR = "Driv_dir"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DOOR_STATE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput01.DoorOpen",
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }

example_obj = ValidationSignals()

@teststep_definition(
    name="State transition Maneuvering to Init door state FR",
    description="In case the front right door is open during maneuvering state, the system shall deactivate the AVG.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class ManToInitDoorOpenFRCheck(TestStep):
    """ManToInitDoorOpenFRCheck Test Step."""

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
        HMI_Info = read_data["State_on_HMI"].tolist()
        door_state = read_data["Door_state"].tolist()
        driving_dir_sig = read_data["Driv_dir"].tolist()
        t1_idx = None
        t2_idx = None

        eval_cond = [True] * 1
        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to Init after the front right door has been open".split()
        )

        """Evaluation part"""
        # Search for the moment when AVG is activated
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t1_idx = cnt
                break
        if t1_idx is not None:
            # Search for the moment when front right open is open
            for _ in range(t1_idx, len(HMI_Info)):
                if door_state[_] == constants.HilCl.Door.DOORSTATE_FRONT_RIGHT_OPEN:
                    t2_idx = _
                    break
            if t2_idx is not None:
                # taking the timestamp of t2_idx in order to check the reaction after 5 sec
                t2_timestamp = time_signal[t2_idx]
                for cnt in range(t2_idx, len(HMI_Info)):
                    if abs(( float(t2_timestamp) - float(time_signal[cnt]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S * 10:
                        t3_idx = cnt
                        break

                if t3_idx is not None:
                    # Check the reaction of the system
                    if HMI_Info[t3_idx] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_CANCELED or driving_dir_sig[t3_idx] != constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                        f" AVG not deactivated (APHMIParkingProcedureCtrlState != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PARKING_CANCELED})"
                        f" or ego vehicle not in standstill (APHMIGeneralDrivingDir != {constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}).".split()
                    )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"TC Failed because the scenario finished before the added delay({10 * constants.DgpsConstants.THRESOLD_TIME_S}s)".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f" front right door is not open (conti_Veh_CAN.VehInput01.DoorOpen != {constants.HilCl.Door.DOORSTATE_FRONT_RIGHT_OPEN}).".split()
                        )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                            f" AVG not activated (APHMIParkingProcedureCtrlState != {constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING} ).".split()
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
            "Check the reaction of the system after FR door is open."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=door_state, mode="lines", name=signal_name["Door_state"]))
        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
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
    name="State transition, Maneuvering to Init - door open FR",
    description="If the front right door is open during maneuvering state, the AVG shall be deactivated.",
    doors_url="https://jazz.conti.de/rm4/resources/BI_xO3QoEQQEe-4oqIAhqwPFA?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F26252",
)
class ManToInitDoorOpenFR(TestCase):
    """ManToInitDoorOpenFR Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ManToInitDoorOpenFRCheck,
        ]
