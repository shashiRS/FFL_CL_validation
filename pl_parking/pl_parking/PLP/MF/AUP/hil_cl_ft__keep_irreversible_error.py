"""Irreversible Error mode, Keep error"""

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

SIGNAL_DATA = "KEEP_IRREVESIBLE_ERROR"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        ISSUE_INDICATOR = "Issue_indicator"
        HMI_INFO = "State_on_HMI"
        IGNITION = "Ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ISSUE_INDICATOR: "CM.vCUS.FTi.Sensor[1].Pdcm.E2E.FrameTimeout",
            self.Columns.HMI_INFO: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIParkingProcedureCtrlState",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="System shall keep error state in case of reaon irreveresible error is not active anymore",
    description="Check system reaction if reason of irreversible is solved during actual ignition cycle.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class AupKeppIrrErrorCheck(TestStep):
    """AupKeppIrrErrorCheck Test Step."""

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
        ignition_sig = read_data["Ignition"].tolist()

        t_ignition_on_idx = None
        t_ignition_off_idx = None
        t_maneuver_idx = None
        t_issue_on_idx = None
        t_issue_off_idx = None
        t_detection_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['State_on_HMI']} signal is PASSED, state of signal switches to PPC_IRREVERSIBLE_ERROR"
            f" ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR}) after USS Timeout injected and stills in this state in whole ignition cycle.".split()
        )

        """Evaluation part"""
        # Find begining of ignition cycle
        for cnt in range(0, len(ignition_sig)):
            if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_ON:
                t_ignition_on_idx = cnt
                break

        if t_ignition_on_idx is not None:

            # Find ignition off
            for cnt in range(t_ignition_on_idx, len(ignition_sig)):
                if ignition_sig[cnt] == constants.HilCl.CarMaker.IGNITION_OFF:
                    t_ignition_off_idx = cnt
                    break

            if t_ignition_off_idx is not None:

                # Find begining of maneuver
                for cnt in range(t_ignition_on_idx, len(state_on_hmi_sig)):
                    if state_on_hmi_sig[cnt] == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING:
                        t_maneuver_idx = cnt
                        break

                if t_maneuver_idx is not None:

                    # Find time point of issue injection
                    for cnt in range(t_maneuver_idx, len(issue_state_sig)):
                        if issue_state_sig[cnt] == constants.HilCl.CarMaker.UssError.TIMEOUT_ENABLED:
                            t_issue_on_idx = cnt
                            break

                    if t_issue_on_idx is not None:

                        # Find issue off
                        for cnt in range(t_issue_on_idx, len(issue_state_sig)):
                            if issue_state_sig[cnt] == constants.HilCl.CarMaker.UssError.TIMEOUT_DISABLED:
                                t_issue_off_idx = cnt
                                break

                        if t_issue_off_idx is not None:

                            if t_issue_off_idx > t_ignition_off_idx:
                                test_result = fc.FAIL
                                self.result.measured_result = FALSE
                                evaluation1 = " ".join(
                                    f"The evaluation of {signal_name['Issue_indicator']} signal is FAILED, signal switches to TIMEOUT_DISABLED ({constants.HilCl.CarMaker.UssError.TIMEOUT_DISABLED})"
                                    f" at {time_signal[t_issue_off_idx]} us but this is after ignition off event ({time_signal[t_ignition_off_idx]} us)."
                                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                                )
                            else:
                                # Find detection
                                for cnt in range(t_ignition_on_idx, t_ignition_off_idx + 1):
                                    if (
                                        state_on_hmi_sig[cnt]
                                        == constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR
                                    ):
                                        t_detection_idx = cnt
                                        break

                                if t_detection_idx is not None:

                                    test_result = fc.PASS
                                    self.result.measured_result = TRUE

                                    # Check keep error part
                                    for cnt in range(t_detection_idx, t_ignition_off_idx + 1):
                                        if (
                                            state_on_hmi_sig[cnt]
                                            != constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR
                                        ):
                                            test_result = fc.FAIL
                                            self.result.measured_result = FALSE
                                            evaluation1 = " ".join(
                                                f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal switches out from PPC_IRREVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR})"
                                                f" at {time_signal[cnt]} us after TIMEOUT_DISABLED ({time_signal[t_issue_off_idx]} us) but end of ignition cycle is {time_signal[t_ignition_off_idx]} us.".split()
                                            )
                                            break

                                else:
                                    test_result = fc.FAIL
                                    self.result.measured_result = FALSE
                                    evaluation1 = " ".join(
                                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_IRREVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR}) after TIMEOUT_ENABLED ({time_signal[t_issue_on_idx]} us) event."
                                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                                    )

                        else:
                            test_result = fc.FAIL
                            self.result.measured_result = FALSE
                            evaluation1 = " ".join(
                                f"The evaluation of {signal_name['Issue_indicator']} signal is FAILED, signal never switched to TIMEOUT_DISABLED ({constants.HilCl.CarMaker.UssError.TIMEOUT_DISABLED}) after TIMEOUT_ENABLED ({time_signal[t_issue_on_idx]} us) event."
                                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                            )

                    else:
                        test_result = fc.FAIL
                        self.result.measured_result = FALSE
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Issue_indicator']} signal is FAILED, signal never switched to TIMEOUT_ENABLED ({constants.HilCl.CarMaker.UssError.TIMEOUT_ENABLED})."
                            " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                        )
                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    evaluation1 = " ".join(
                        f"The evaluation of {signal_name['State_on_HMI']} signal is FAILED, signal never switched to PPC_PERFORM_PARKING ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_PERFORM_PARKING})."
                        " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                    )

            else:
                test_result = fc.FAIL
                self.result.measured_result = FALSE
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['Ignition']} signal is FAILED, signal never switched to IGNITION_OFF ({constants.HilCl.CarMaker.IGNITION_OFF}) after ignition on event ({time_signal[t_ignition_on_idx]} us)."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            self.result.measured_result = FALSE
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['Ignition']} signal is FAILED, signal never switched to IGNITION_ON ({constants.HilCl.CarMaker.IGNITION_ON})."
                " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
            )

        signal_summary[
            f"System shall switch to PPC_IRREVERSIBLE_ERROR ({constants.HilCl.Hmi.ParkingProcedureCtrlState.PPC_IRREVERSIBLE_ERROR}) and still in this state in actual ignition cycle"
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED"""
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=state_on_hmi_sig, mode="lines", name=signal_name["State_on_HMI"]))
            fig.add_trace(go.Scatter(x=time_signal, y=ignition_sig, mode="lines", name=signal_name["Ignition"]))
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
    name="Keep irreversible error state in whole ignition cycle",
    description="The AP Function shall keep the irreversible error until the ego vehicle is restarted.",
)
class AupKeppIrrError(TestCase):
    """AupKeppIrrError Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            AupKeppIrrErrorCheck,
        ]
