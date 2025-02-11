"""Driver interaction with the vehicle during RA, Display the visual indication that the vehicle is moving in reverse"""

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

SIGNAL_DATA = "RA_INF_ABOUT_BACK"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        DRIVING_DIR = "Driv_dir"
        GENERAL_SCREEN = "General_screen"
        GEAR = "Gear"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.DRIVING_DIR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDrivingDir",
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.GEAR: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralCurrentGear",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Indication check",
    description="Check system display the visual indication that the vehicle is moving in reverse",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class CommonRaInfRevCheck(TestStep):
    """CommonRaInfRevCheck Test Step."""

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
        general_scrren_sig = read_data["General_screen"].tolist()
        driving_dir_sig = read_data["Driv_dir"].tolist()
        gear_sig = read_data["Gear"].tolist()

        t1_idx = None
        t2_idx = None

        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Driv_dir']} signal is PASSED, signal is DRIVING_BACKWARDS"
            f" ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.DRIVING_BACKWARDS}) while RA is active and gear is set to R.".split()
        )

        """Evaluation part"""

        # Find when RA switches to active
        for cnt, value in enumerate(general_scrren_sig):
            if value == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t1_idx = cnt
                break

        if t1_idx is not None:
            # Find when RA switches out from active state
            for cnt in range(t1_idx, len(general_scrren_sig)):
                if general_scrren_sig[cnt] != constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                    t2_idx = cnt
                    break

            if t2_idx is not None:
                eval_cond = [True] * 1
                # Check system info during RA when gear == R
                for cnt in range(t1_idx, t2_idx):
                    if (
                        driving_dir_sig[cnt] != constants.HilCl.Hmi.APHMIGeneralDrivingDir.DRIVING_BACKWARDS
                        and gear_sig[cnt] == constants.HilCl.Gear.GEAR_R
                    ):
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal is not DRIVING_BACKWARDS"
                            f" ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.DRIVING_BACKWARDS}) at {time_signal[cnt]} us but RA is active"
                            f" ({signal_name['General_screen']} == REVERSE_ASSIST [{constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST}]) and actual gear is GEAR_R ({constants.HilCl.Gear.GEAR_R}).".split()
                        )
                        eval_cond[0] = False
                        break

                    if (
                        driving_dir_sig[cnt] == constants.HilCl.Hmi.APHMIGeneralDrivingDir.DRIVING_BACKWARDS
                        and gear_sig[cnt] != constants.HilCl.Gear.GEAR_R
                    ):
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Driv_dir']} signal is FAILED, signal is DRIVING_BACKWARDS"
                            f" ({constants.HilCl.Hmi.APHMIGeneralDrivingDir.DRIVING_BACKWARDS}) at {time_signal[cnt]} us but RA is active"
                            f" ({signal_name['General_screen']} == REVERSE_ASSIST [{constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST}]) and actual gear is not GEAR_R ({constants.HilCl.Gear.GEAR_R}).".split()
                        )
                        eval_cond[0] = False
                        break

            else:
                test_result = fc.FAIL
                eval_cond = [False] * 1
                evaluation1 = " ".join(
                    f"The evaluation of {signal_name['General_screen']} signal is FAILED, signal never switched out from REVERSE_ASSIST ({constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST})."
                    " It is not possible to continue evaluation in this case. This event is needed to evaluation.".split()
                )

        else:
            test_result = fc.FAIL
            eval_cond = [False] * 1
            evaluation1 = " ".join(
                f"The evaluation of {signal_name['General_screen']} signal is FAILED, signal never switched to REVERSE_ASSIST ({constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST})."
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
            "During automated reversing mode, the function shall display the visual indication that the vehicle is moving in reverse."
        ] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=time_signal, y=general_scrren_sig, mode="lines", name=signal_name["General_screen"])
            )
            fig.add_trace(go.Scatter(x=time_signal, y=driving_dir_sig, mode="lines", name=signal_name["Driv_dir"]))
            fig.add_trace(go.Scatter(x=time_signal, y=gear_sig, mode="lines", name=signal_name["Gear"]))

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
    name="Driver interaction with the vehicle during RA, Indicate reverse moving",
    description="During automated reversing mode, the function shall display the visual indication that the vehicle is moving in reverse.",
)
class CommonRaInfRev(TestCase):
    """CommonRaInfRev Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            CommonRaInfRevCheck,
        ]
