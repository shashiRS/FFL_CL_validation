"""Irreversible error mode."""

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

SIGNAL_DATA = "IRREVESIBLE_ERROR_MODE"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        ISSUE_INDICATOR = "Issue_indicator"
        HMI_INFO = "State_on_HMI"
        GEAR = "Gear"
        PARK_BRAKE = "Park_brake"
        DRIV_DIR = "Driv_dir"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ISSUE_INDICATOR: "CM.vCUS.FTi.Sensor[1].Pdcm.E2E.FrameTimeout",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GEAR: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.PARK_BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.Brake.ParkBrake",
            self.Columns.DRIV_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="System reaction on irreversible error. Irreversible error mode.",
    description="Check system reaction on USS timeout",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupIrrErrorModeCheck(TestStep):
    """AupIrrErrorModeCheck Test Step."""

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
        issue_state_sig = read_data["Issue_indicator"].tolist()
        gear_sig = read_data["Gear"].tolist()
        park_brake_sig = read_data["Park_brake"].tolist()
        driv_dir_sig = read_data["Driv_dir"].tolist()

        t_maneuvering_idx = None
        t_issue_idx = None
        t_detection_idx = None

        t_gear_p = None
        t_park_brake_idx = None
        t_standstill_idx = None

        evaluation1 = " ".join(
            f"The evaluation is PASSED."
            f"<br> - state of {signal_name['State_on_HMI']} signal switches to PPC_IRREVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR})"
            f"<br> - state of {signal_name['Gear']} signal swithces to PARK_ACTUALGEAR ({constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR})"
            f"<br> - state of {signal_name['Park_brake']} signal swithces to ACTIVE_PARKBRAKE ({constants.HilCl.Brake.PARK_BRAKE_SET})"
            f"<br> - state of {signal_name['Driv_dir']} signal swithces to PARK_ACTUALGEAR ({constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR})"
            f"<br> in range of 10 seconds after USS Timeout injection.".split()
        )

        """Evaluation part"""
        # Find begining of Maneuvering
        for cnt, item in enumerate(state_on_hmi_sig):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_maneuvering_idx = cnt
                break

        if t_maneuvering_idx is not None:

            # Find issue injection time
            for cnt in range(t_maneuvering_idx, len(issue_state_sig)):
                if issue_state_sig[cnt] == constants.HilCl.CarMaker.UssError.TIMEOUT_ENABLED:
                    t_issue_idx = cnt
                    break

            if t_issue_idx is not None:
                # Check signal states
                eval_cond = [True] * 4
                counter = 0

                # Collect states of signal
                states_dict = HilClFuntions.States(state_on_hmi_sig, t_maneuvering_idx, len(state_on_hmi_sig), 1)

                # Keys contains the idx
                # Check mode after Maneuvering mode
                for key in states_dict:
                    if counter == 1:
                        actual_value = constants.HilCl.Hmi.ParkingProcedureCtrlState.DICT_CTRL_STATE.get(
                            states_dict[key]
                        )
                        actual_number = int(states_dict[key])

                        if key < t_issue_idx:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to {actual_value} ({actual_number}) at {time_signal[key]} us"
                                f" before USS Timeout injection.".split()
                            )
                            eval_cond[0] = False
                            break

                        if states_dict[key] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR:
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, state of signal is {actual_value} ({actual_number}) at {time_signal[key]} us"
                                f" but requiered mode is PPC_IRREVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR}).".split()
                            )
                            eval_cond[0] = False
                            break
                        else:
                            # Store idx of reversible error detection
                            t_detection_idx = key

                        counter += 1
                    else:
                        counter += 1

                # Check detection and secured state reaction time
                # Error detection
                if t_detection_idx is not None:
                    time_gap = time_signal[t_detection_idx] - time_signal[t_issue_idx]
                    if (
                        time_gap > 10 * 1e6
                    ):  # Number is defined by Originator of Test Case Design. Not neede to add to constants.py because this value is used just here.
                        eval_cond[0] = False

                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches to PPC_IRREVERSIBLE_ERROR"
                            f" ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR}) at {time_signal[t_detection_idx]} us but the time gap between error detection and"
                            f" issue injection is {time_gap * 1e-6} seconds but requiered time is lass then 10 seconds.".split()
                        )

                # Gear
                for cnt in range(t_issue_idx, len(gear_sig)):
                    if gear_sig[cnt] == constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR:
                        t_gear_p = cnt
                        break
                if t_gear_p is not None:

                    time_gap = time_signal[t_gear_p] - time_signal[t_issue_idx]
                    if (
                        time_gap > 10 * 1e6
                    ):  # Number is defined by Originator of Test Case Design. Not neede to add to constants.py because this value is used just here.
                        eval_cond[1] = False

                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Gear']} signal is FAILED, signal switches to PARK_ACTUALGEAR"
                            f" ({{constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR}}) at {time_signal[t_gear_p]} us but the time gap between PARK_ACTUALGEAR and"
                            f" issue injection is {time_gap * 1e-6} seconds but requiered time is lass then 10 seconds.".split()
                        )

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Gear']} signal is FAILED, signal did not switch to PARK_ACTUALGEAR ({constants.HilCl.VehCanActualGear.PARK_ACTUALGEAR}) after issue injection."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

                # Parking brake
                for cnt in range(t_issue_idx, len(park_brake_sig)):
                    if park_brake_sig[cnt] == constants.HilCl.Brake.PARK_BRAKE_SET:
                        t_park_brake_idx = cnt
                        break

                if t_park_brake_idx is not None:

                    time_gap = time_signal[t_park_brake_idx] - time_signal[t_issue_idx]
                    if (
                        time_gap > 10 * 1e6
                    ):  # Number is defined by Originator of Test Case Design. Not neede to add to constants.py because this value is used just here.
                        eval_cond[2] = False

                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Park_brake']} signal is FAILED, signal switches to ACTIVE_PARKBRAKE"
                            f" ({constants.HilCl.Brake.PARK_BRAKE_SET}) at {time_signal[t_park_brake_idx]} us but the time gap between ACTIVE_PARKBRAKE and"
                            f" issue injection is {time_gap * 1e-6} seconds but requiered time is lass then 10 seconds.".split()
                        )

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Park_brake']} signal is FAILED, signal did not switch to ACTIVE_PARKBRAKE ({constants.HilCl.Brake.PARK_BRAKE_SET}) after issue injection."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

                # Standstill
                for cnt in range(t_issue_idx, len(driv_dir_sig)):
                    if driv_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                        t_standstill_idx = cnt
                        break

                if t_standstill_idx is not None:

                    time_gap = time_signal[t_standstill_idx] - time_signal[t_issue_idx]
                    if (
                        time_gap > 10 * 1e6
                    ):  # Number is defined by Originator of Test Case Design. Not neede to add to constants.py because this value is used just here.
                        eval_cond[3] = False

                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal switches to STANDSTILL"
                            f" ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}) at {time_signal[t_standstill_idx]} us but the time gap between STANDSTILL and"
                            f" issue injection is {time_gap * 1e-6} seconds but requiered time is lass then 10 seconds.".split()
                        )

                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal did not switch to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}) after issue injection."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Issue_indicator']} signal is FAILED, signal never switched to TIMEOUT_ENABLED ({constants.HilCl.CarMaker.UssError.TIMEOUT_ENABLED})."
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
            "System shall indicate irreversible error on HMI and reach secured state in range of 10 seconds."
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
            fig.add_trace(go.Scatter(x=time_signal, y=park_brake_sig, mode="lines", name=signal_name["Park_brake"]))
            fig.add_trace(go.Scatter(x=time_signal, y=driv_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
            fig.add_trace(
                go.Scatter(x=time_signal, y=issue_state_sig, mode="lines", name=signal_name["Issue_indicator"])
            )

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
    name="Irreversible error mode description.",
    description="If the previous mode was Maneuvering then the function shall request braking"
    " the vehicle to standstill and request securing the vehicle from rolling away. Afterwards the function shall release all active control.",
)
class AupIrrErrorMode(TestCase):
    """AupIrrErrorMode Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupIrrErrorModeCheck,
        ]
