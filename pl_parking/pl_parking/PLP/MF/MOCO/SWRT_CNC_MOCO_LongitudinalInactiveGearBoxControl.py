"""moco longitudinal inactive gearbox control"""

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
    tag,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MoCoSignals

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.1"
__status__ = "Development"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "SWRT_CNC_MOCO_LongitudinalInactiveGearBoxControl"

signals_obj = MoCoSignals()


@teststep_definition(step_number=1, name="KPI", description=" ", expected_result=BooleanResult(FALSE))
@register_signals(ALIAS, MoCoSignals)
class Step1(TestStep):
    """moco longitudinal inactive gearbox control test setup"""

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
            df = self.readers[ALIAS]

            if (df["activateLoCtrl"] == 0).any():
                df["match"] = (df["activateLoCtrl"] == 0) & (df["gearboxCtrlRequest_nu"] == 0)

                total = df[(df["activateLoCtrl"] == 0) | (df["gearboxCtrlRequest_nu"] == 0)].shape[0]
                match = df["match"].sum()
                percent_match = (match / total) * 100 if total > 0 else 0

                if percent_match == 100:
                    observed_la_dmc_ctrl_request_nu = TRUE
                    test_result = fc.PASS
                    eval_text = " ".join(
                        f"The component has not set gearboxCtrlRequestPort.gearboxCtrlRequest_nu to false"
                        f" Conditions: {test_result}.".split()
                    )

                else:
                    observed_la_dmc_ctrl_request_nu = FALSE
                    test_result = fc.FAIL
                    eval_text = " ".join(
                        f"The component has set gearboxCtrlRequestPort.gearboxCtrlRequest_nu to false"
                        f" Conditions: {test_result}.".split()
                    )

                self.result.measured_result = observed_la_dmc_ctrl_request_nu
                eval_0 = " ".join(
                    "Ensure that the component does not activate gear box control as long as the input request signal is not active.".split()
                )

                # Set table dataframe
                signal_summary = pd.DataFrame(
                    {
                        "Evaluation": {
                            "1": eval_0,
                        },
                        "Result": {
                            "1": eval_text,
                        },
                    }
                )

                sig_sum = fh.build_html_table(signal_summary)
                fig = go.Figure()
                plot_titles.append("")
                plots.append(sig_sum)
                remarks.append("")

                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["activateLoCtrl"].values.tolist(),
                        mode="lines",
                        name="activateLoCtrl",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index.values.tolist(),
                        y=df["gearboxCtrlRequest_nu"].values.tolist(),
                        mode="lines",
                        name="gearboxCtrlRequest_nu",
                    )
                )

                fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="MTS.Package.Timestamp"
                )
                fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
                plot_titles.append("Graphical Overview")
                plots.append(fig)
                remarks.append("")

                additional_results_dict = {
                    "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                    "Percent match [%]": {"value": percent_match},
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
            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = NAN
                self.result.details["Step_result"] = test_result
                eval_0 = " ".join(
                    "Ensure that the component does not activate gear box control as "
                    "long as the input request signal is not active".split()
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
                for plot in plots:
                    if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                        self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                    else:
                        self.result.details["Plots"].append(plot)
                for plot_title in plot_titles:
                    self.result.details["Plot_titles"].append(plot_title)
                for remark in remarks:
                    self.result.details["Remarks"].append(remark)
                additional_results_dict = {
                    "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                    "Percent match [%]": {"value": "n/a"},
                }
                self.result.details["Additional_results"] = additional_results_dict

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

@tag("SWRT_CNC_MOCO_LongitudinalInactiveGearBoxControl")
@verifies("1407046")
@testcase_definition(
    name="MOCO Longitudinal inactive gearbox control",
    group="longitudinal",
    description="Ensure that the component does not activate gear box control as long as the input request signal is not active.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SWRT_CNC_MOCO_LongitudinalInactiveGearBoxControl(TestCase):
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
    test_bsigs = [r".\absolute_directory_path_to_your_measurement\file.erg"]

    debug(
        SWRT_CNC_MOCO_LongitudinalInactiveGearBoxControl,
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
