"""Show distance to stop during RA maneuver"""

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

SIGNAL_DATA = "RA_DISTANCE_TO_STOP"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        GENERAL_SCREEN = "General_screen"
        DISTANCE_TO_STOP = "Dis_to_stop"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GENERAL_SCREEN: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralScreen",
            self.Columns.DISTANCE_TO_STOP: "MTS.AP_Private_CAN.AP_Private_CAN.APHMIInGeneral1.APHMIGeneralDistToStop",
        }


example_obj = ValidationSignals()


@teststep_definition(
    name="Distance to stop indicatio check during RA",
    description="Check distance to stop indication during the whole RA maneuver",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class RaDisToStopCheck(TestStep):
    """RaDisToStopCheck Test Step."""

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
        screen_sig = read_data["General_screen"].tolist()
        distance_sig = read_data["Dis_to_stop"].tolist()

        t_begining_idx = None
        t_end_idx = None
        evaluation1 = " ".join(
            f"The evaluation of {signal_name['Dis_to_stop']} signal is PASSED, system indicated the disctance to stop during the whole RA maneuver.".split()
        )

        """Evaluation part"""
        # Find begining and end of RA maneuver
        for cnt, item in enumerate(screen_sig):
            if item == constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                t_begining_idx = cnt
                break

        if t_begining_idx is not None:

            # Find end of RA maneuver
            for cnt in range(t_begining_idx, len(screen_sig)):
                if screen_sig[cnt] != constants.HilCl.Hmi.APHMIGeneralScreen.REVERSE_ASSIST:
                    t_end_idx = cnt
                    break

            if t_end_idx is not None:
                eval_cond = [True] * 1
                # Collect distance related signal values during RA maneuver
                prevoius_value = None
                trend = []

                for cnt in range(t_begining_idx, t_end_idx + 1):
                    if cnt == t_begining_idx:
                        prevoius_value = distance_sig[cnt]
                        continue
                    else:
                        trend.append(prevoius_value - distance_sig[cnt])
                        prevoius_value = distance_sig[cnt]

                # Check recrease in value
                for item in trend:
                    if item < 0:
                        evaluation1 = " ".join(
                            f"The evaluation of {signal_name['Dis_to_stop']} signal is FAILED. There is an increase trend in value of signal during RA maneuver."
                            " Distance to stop shall not increase during RA maneuver.".split()
                        )
                        eval_cond[0] = False

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

        signal_summary["Distance to stop presentation during RA"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """
        if test_result == fc.FAIL:

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=time_signal, y=screen_sig, mode="lines", name=signal_name["General_screen"]))
            fig.add_trace(go.Scatter(x=time_signal, y=distance_sig, mode="lines", name=signal_name["Dis_to_stop"]))

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
    name="Distance to stop presentation during Reverse Assist maneuver",
    description="While being in the automated reversing mode, the RA function shall indicate and update the distance to stop to the driver.",
)
class RaDisToStop(TestCase):
    """RaDisToStop Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            RaDisToStopCheck,
        ]
