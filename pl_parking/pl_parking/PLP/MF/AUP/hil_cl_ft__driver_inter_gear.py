"""Driver Intervention, Manually changes the gear"""

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

SIGNAL_DATA = "DRIVER_INTERVETION_MANUAL_GEAR_SHIFT"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        HMI_INFO = "State_on_HMI"
        CURRENT_GEAR = "Current_gear"
        DRIV_DIRECTION = "Driv_dir"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.CURRENT_GEAR: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.DRIV_DIRECTION: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Driver Intervention, Manually changes the gear",
    description="Check system reaction if driver manually shift gear during AVG.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupDrivIntgearCheck(TestStep):
    """AupDrivIntgearCheck Test Step."""

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
        gear_sig = read_data["Current_gear"].tolist()
        driv_dir_sig = read_data["Driv_dir"].tolist()

        t_maneuvering_idx = None
        t_gear_shift_idx = None
        t_standstill_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Driv_dir']} signal is PASSED, signal switches to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})"
            f" in 5 seconds after gear shift event.".split()
        )

        """Evaluation part"""
        # Find begining of parking
        for cnt, item in enumerate(state_on_hmi_sig):
            if item == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                t_maneuvering_idx = cnt
                break

        if t_maneuvering_idx is not None:

            # Find when gear shifted to predefined state

            for cnt in range(t_maneuvering_idx, len(gear_sig)):
                if gear_sig[cnt] == constants.HilCl.VehCanActualGear.NINTH_ACTUALGEAR:
                    t_gear_shift_idx = cnt
                    break

            if t_gear_shift_idx is not None:
                # Find standstill after gear shift
                for cnt in range(t_gear_shift_idx, len(driv_dir_sig)):
                    if driv_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL:
                        t_standstill_idx = cnt
                        break

                if t_standstill_idx is not None:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE

                    # Set treshold to us
                    treshold_in_us = constants.HilCl.ApThreshold.TRESHOLD_TO_STANDSTILL * 1e6

                    # Calculate time to stop from event
                    delta_time = time_signal[t_standstill_idx] - time_signal[t_gear_shift_idx]

                    # Compare with treshold
                    if delta_time > treshold_in_us:
                        test_result = fc.FAIL
                        self.result.measured_result = FALSE
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Driv_dir']} signal is FAIL, signal switches to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL})"
                            f" after {signal_name['Current_gear']} signal switched to NINTH_ACTUALGEAR ({constants.HilCl.VehCanActualGear.NINTH_ACTUALGEAR})"
                            f" but delta time between connection and standstill is {delta_time} us and treshold is {treshold_in_us} us.".split()
                        )

                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['Driv_dir']} signal is FAIL, signal never switched to STANDSTILL ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.STANDSTILL}) mode after manualy gear shift event."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                self.result.measured_result = FALSE
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Current_gear']} signal is FAIL, signal never switched to NINTH_ACTUALGEAR ({constants.HilCl.VehCanActualGear.NINTH_ACTUALGEAR}) mode."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['State_on_HMI']} signal is FAIL, signal never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING}) mode."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        signal_summary["Vehicle state deactivation, Set trunk to open during active parking maneuver"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAIL """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=driv_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
            fig.add_trace(go.Scatter(x=time_signal, y=gear_sig, mode="lines", name=signal_name["Current_gear"]))

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
    name="Driver Intervention, Manually changes the gear",
    description="A driver intervention is present as long as the driver manually changes the gear lever during an active AVG Maneuver",
)
class AupDrivIntgear(TestCase):
    """AupDrivIntgear Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupDrivIntgearCheck,
        ]
