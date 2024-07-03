"""moco general signal status"""

#!/usr/bin/env python3

import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import FALSE, NAN, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

from pl_parking.common_ft_helper import MoCoStatusSignals
import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants

from pl_parking.PLP.MF.MOCO.helpers import count_e_signal_status_signal

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Development"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "SWT_swrt_cnc_moco_general_signal_status"

signals_obj = MoCoStatusSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(TRUE))
@register_signals(ALIAS, MoCoStatusSignals)
class Step1(TestStep):
    """general signal status test step"""

    custom_report = fh.MOCOCustomTeststepReport

    def __init__(self):
        """Initialsie the test step"""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            plot_titles, plots, remarks = fh.rep([], 3)
            test_result = fc.INPUT_MISSING
            self.result.measured_result = NAN

            try:
                df = self.readers[ALIAS].signals
            except Exception as e:
                print(str(e))
                df = self.readers[ALIAS]

            num_signal = count_e_signal_status_signal(df)
            """Checking if the signals are present"""
            if num_signal:
                assertion_dict = []
                fig = go.Figure()
                for _, row in df.iterrows():
                    for i in num_signal:
                        signal_key = i
                        if row[signal_key] != constants.MoCo.Parameter.AL_SIG_STATE_OK:
                            assertion_dict.append((row[0], signal_key, row[signal_key]))

                for i in num_signal:
                    fig.add_trace(
                        go.Scatter(x=df.index.values.tolist(), y=df[i], mode="lines", name=f"{i}", visible="legendonly")
                    )
                eval_0 = " ".join(
                    "Signal state of all output ports shall be OK after component initialization "
                    "for valid inputs and connected input and output ports".split()
                )

                # Set table dataframe
                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "1": eval_0,
                        },
                    }
                )
                sig_sum = fh.build_html_table(signal_summary)
                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")
                if assertion_dict:
                    "Table commented out and removed from test report"
                    "used it with few failed timestamps as part of the analysis"
                    # assert_summary = pd.DataFrame({'ERROR': {key: f'Timestamp: {key[0]} Signal: {key[1]} with value {key[2]}'
                    #                                          for key in assertion_dict}})
                    # assert_summary = fh.build_html_table(assert_summary)
                    # plot_titles.append("")
                    # plots.append(assert_summary)
                    # remarks.append("")

                    self.result.measured_result = FALSE
                    test_result = fc.FAIL
                else:
                    self.result.measured_result = TRUE
                    test_result = fc.PASS
            else:
                self.result.measured_result = FALSE
                test_result = fc.FAIL
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("Graphical Overview")
            plots.append(fig)
            remarks.append("")

            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                # "Percent match [%]": {"value": percent_match},
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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("1665879")
@testcase_definition(
    name="MoCo General SignalStatus",
    group="general status",
    description="Ensure that the signal state of all output ports shall be OK after component "
    "initialization for valid inputs and connected input and output ports",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class SWT_swrt_cnc_moco_general_signal_status(TestCase):
    """Example test case."""

    custom_report = fh.MOCOCustomTestCase

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            Step1,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    # Define your directory path to your measurements for debugging purposes
    test_bsigs = [r"D:\MOCO\AP_SmallRegressionTests_20240319\AUPSim_UC_AngLeft_ST-0562_F_SI_On_03.erg"]

    debug(
        SWT_swrt_cnc_moco_general_signal_status,
        *test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )
    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
