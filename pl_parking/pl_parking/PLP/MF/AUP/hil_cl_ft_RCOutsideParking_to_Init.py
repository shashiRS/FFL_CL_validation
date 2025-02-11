"""Ego vehicle shall transit from RC Outside ParkOut to Init after dist is > {AP_G_ROLLED_DIST_OUT_THRESH_M}m."""
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

SIGNAL_DATA = "RCOUTPARK_TO_INIT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        USEER_ACTION_REM = "User_action"
        HMI_INFO = "State_on_HMI"
        GEAR = "Gear"
        BRAKE = "Brake"
        CAR_HITCH_X = "Car_hitch_x"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.USEER_ACTION_REM: "MTS.IO_CAN_AP_Private_CAN.APHMIOut1.APHMIOutUserActionRem",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.GEAR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralCurrentGear",
            self.Columns.BRAKE: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput06.BrakePressureDriver",
            self.Columns.CAR_HITCH_X: "CM.Car.Hitch.tx",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Transition mode check",
    description="Check if the system transit to Init from RC ParkOut after dist is > {AP_G_ROLLED_DIST_OUT_THRESH_M}m.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RCOutsideParkingToInitCheck(TestStep):
    """RCOutsideParkingToInitCheck Test Step."""

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
        user_act_rem = read_data["User_action"].tolist()
        HMI_Info = read_data["State_on_HMI"].tolist()
        Gear = read_data["Gear"].tolist()
        Brake = read_data["Brake"].tolist()
        car_hitch_x = read_data["Car_hitch_x"].tolist()
        start_rolling_pos = None

        t1_idx = None
        t2_idx = None
        t3_idx = None
        t4_idx = None

        evaluation1 = " ".join(
            f"The evaluation of AVG State {signal_name['State_on_HMI']} signal is PASSED,"
            f" signal switches to PPC_BEHAVIOR_INACTIVE - ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE})"
            f" after the distance is >= AP_G_ROLLED_DIST_OUT_THRESH_M.".split()
        )

        """Evaluation part"""
        # Find the moment when the system is in RC Outside Parking Out  ( ParkingProcedureCtrlState = PPC_SCANNING_OUT)
        for cnt in range(0, len(HMI_Info)):
            if HMI_Info[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT:
                t1_idx = cnt
                break

        if t1_idx is not None:
            eval_cond = [True] * 1

            # Find the moment when gear pos is switched to Neutral and brake pedal is released and save the position
            for cnt in range(t1_idx, len(user_act_rem)):
                if Gear[cnt] == constants.HilCl.Gear.GEAR_N and Brake[cnt] < 0.01 :
                    t2_idx = cnt
                    start_rolling_pos = car_hitch_x[cnt]
                    break

            if t2_idx is not None:
                # search for the moment when the distance is >= AP_G_ROLLED_DIST_OUT_THRESH_M
                for i in range (t1_idx, len(car_hitch_x)):
                    if start_rolling_pos - car_hitch_x[i] >= constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_OUT_THRESH_M:
                        t3_idx = i
                        break

                if t3_idx is not None:
                    # check between t1_idx and t3_idx if AVG have a constant PPC_SCANNING_OUT state
                    for i in range(t1_idx,t3_idx):
                        if HMI_Info[i] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                                " AVG not in RC Outside Parking Out state before start moving.".split()
                            )
                            break
                    # taking the timestamp of t3_idx in order to check the reaction 0.5s after
                    t3_timestamp = time_signal[t3_idx]
                    for cnt in range(t3_idx, len(HMI_Info)):
                        if abs(( float(t3_timestamp) - float(time_signal[cnt]) ) / 10**6) > constants.DgpsConstants.THRESOLD_TIME_S:
                            t4_idx = cnt
                            break
                    # check if after 0.5s the AVG start the parking maneuver
                    if t4_idx is not None:
                        if HMI_Info[t4_idx] != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_BEHAVIOR_INACTIVE:
                            test_result = fc.FAIL
                            eval_cond = [False] * 1
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                                f" AVG didn't deactivate after {constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_OUT_THRESH_M}m + 0.5s delay.".split()
                            )
                    else:
                        test_result = fc.FAIL
                        eval_cond = [False] * 1
                        evaluation1 = " ".join(
                            f"TC Failed because the scenario finished before the delay finished ({constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_OUT_THRESH_M})".split()
                        )
                else:
                    test_result = fc.FAIL
                    eval_cond = [False] * 1
                    evaluation1 = " ".join(
                        f" TC Failed because ego car didn't exceed the min dist of {constants.HilCl.ApThreshold.AP_G_ROLLED_DIST_OUT_THRESH_M}m.".split()
                    )
            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                    f" brake not released({signal_name['Brake']} != 0) and gear pos not set to Neutral({signal_name['Gear']}!={constants.HilCl.Gear.GEAR_N})".split()
                )
        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED,"
                f" AVG didn't reach the RC Outside ParkingOut state({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_SCANNING_OUT}).".split()
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
            "Check the reaction of the system while RC OutsidePark"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart """

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=time_signal, y=user_act_rem, mode="lines", name=signal_name["User_action"]))
        fig.add_trace(go.Scatter(x=time_signal, y=HMI_Info, mode="lines", name=signal_name["State_on_HMI"]))
        fig.add_trace(go.Scatter(x=time_signal, y=Gear, mode="lines", name=signal_name["Gear"]))
        fig.add_trace(go.Scatter(x=time_signal, y=Brake, mode="lines", name=signal_name["Brake"]))
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
    name="RC OutsideParking to Init",
    description="The function shall transit to Init in case the car start the movement and dist is >={AP_G_ROLLED_DIST_OUT_THRESH_M} from RC Outside Parking Out state",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_5N7DKRS-Ee6D0fn3IY9AdA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
class RCOutsideParkingToInit(TestCase):
    """RCOutsideParkingToInit Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RCOutsideParkingToInitCheck,
        ]
