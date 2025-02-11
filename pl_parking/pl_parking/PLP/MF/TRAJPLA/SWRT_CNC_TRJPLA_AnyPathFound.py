"""SWRT_CNC_TRJPLA_AnyPathFound.py
Test Scenario: Parkin/ParkOut scenario with multiple poses, where only some of the poses are fully reachable
"""

import logging
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals
from pl_parking.PLP.MF.constants import ConstantsTrajpla as trajpla

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
import tempfile
from pathlib import Path

from tsf.core.utilities import debug

SIGNAL_DATA = "MF_ANY_PATH_FOUND"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Target pose fully reachable status",
    description=(
        "If there is at least one fully reachable target pose, TRJPLA shall send targetPosesPort.anyPathFound = true."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaAnyPathFound(TestStep):
    """Defining teststep"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """  # required docstring
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)
        try:
            evaluation = ""
            signals = self.readers[SIGNAL_DATA]

            signal_summary = {}
            signal_name = example_obj._properties
            frame_data_dict = {}
            test_result_dict = {}
            num_valid_poses = signals["numValidPoses"]
            anypath_found = signals["anyPathFound"]
            reachable_status = {}
            for idx in range(8):
                reachable_status[idx] = signals[f"targetPoseReachableStatus{idx}"]
                signals[f"ReachableStatus{idx}"] = reachable_status[idx].apply(
                    lambda x: fh.get_status_label(x, trajpla.ReachableStatus)
                )

            for idx in range(len(reachable_status[0])):
                eval_cond = False
                if num_valid_poses.iloc[idx] > 0:
                    for p_idx in range(int(num_valid_poses.iloc[idx])):
                        if reachable_status[p_idx].iloc[idx] == trajpla.ReachableStatus.TP_FULLY_REACHABLE:
                            eval_cond = True
                            break
                    if eval_cond is True:
                        if anypath_found.iloc[idx] == 1:
                            test_result_dict[idx] = True
                            frame_data_dict[idx] = "Pass"
                        else:
                            if not evaluation:
                                evaluation = " ".join(
                                    f"The evaluation of {signal_name['anyPathFound']} and is FAILED, at frame "
                                    f" {idx}.".split()
                                )
                            test_result_dict[idx] = False
                            frame_data_dict[idx] = "Fail : anyPathFound not set despite availability of reachable pose"
                    else:
                        test_result_dict[idx] = None
                        frame_data_dict[idx] = "NA: No reachable poses available"
                else:
                    test_result_dict[idx] = None
                    frame_data_dict[idx] = "NA: Valid poses not available"

            if False in test_result_dict.values():
                verdict = fc.FAIL
                self.result.measured_result = FALSE
            elif list(test_result_dict.values()) == [None] * len(test_result_dict.values()):
                verdict = fc.FAIL
                self.result.measured_result = FALSE
                if not evaluation:
                    evaluation = "Evaluation not possible, valid or reachable poses are not available"
            else:
                verdict = fc.PASS
                self.result.measured_result = TRUE
                evaluation = "Passed"

            expected_val = "AP.targetPosesPort.anyPathFound == 1"

            signal_summary[
                f"{signal_name['anyPathFound']} = true, when any one of the target poses is TP_FULLY_REACHABLE"
            ] = [expected_val, evaluation, verdict]

            remark = " ".join(
                f"{signal_name['anyPathFound']} = true, when any one of the target poses is TP_FULLY_REACHABLE".split()
            )
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            frame_number_list = list(range(0, len(anypath_found)))
            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=anypath_found,
                    mode="lines",
                    name=signal_name["anyPathFound"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=num_valid_poses,
                    mode="lines",
                    name=signal_name["numValidPoses"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            for i in range(int(max(num_valid_poses))):
                fig.add_trace(
                    go.Scatter(
                        x=frame_number_list,
                        y=reachable_status[i],
                        mode="lines",
                        name="reachableStatus" + str(i),
                        hovertemplate="Frame: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                        text=signals[f"ReachableStatus{i}"],
                    )
                )
            if True in test_result_dict.values() or False in test_result_dict.values():
                fig.add_trace(
                    go.Scatter(
                        x=frame_number_list,
                        y=[0] * len(frame_number_list),
                        mode="lines",  # 'lines' or 'markers'
                        name="Test Status",
                        hovertemplate="Frame: %{x}<br><br>status: %{text}<extra></extra>",
                        text=list(frame_data_dict.values()),
                    )
                )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Frames",
                title="Graphical Overview of Evaluated signals",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)

            res_valid = (np.array(list(test_result_dict.values()))) != np.array(None)
            res_valid_int = [int(elem) for elem in res_valid]
            res_valid_int.insert(0, 0)
            eval_start = [i - 1 for i in range(1, len(res_valid_int)) if res_valid_int[i] - res_valid_int[i - 1] == 1]
            eval_stop = [i - 1 for i in range(1, len(res_valid_int)) if res_valid_int[i] - res_valid_int[i - 1] == -1]
            if len(eval_start) > 0:
                for i in range(len(eval_start)):
                    fig.add_vline(
                        x=eval_start[i],
                        line_width=1,
                        line_dash="dash",
                        line_color="darkslategray",
                        annotation_text=f"t{i + 1}Start",
                    )
            if len(eval_stop) > 0:
                for i in range(len(eval_stop)):
                    fig.add_vline(
                        x=eval_stop[i],
                        line_width=1,
                        line_dash="dash",
                        line_color="darkslategray",
                        annotation_text=f"t{i + 1}Stop",
                    )
            plots.append(fig)

            result_df = {
                "Verdict": {"value": verdict, "color": fh.get_color(verdict)},
                fc.REQ_ID: ["1492142"],
                fc.TESTCASE_ID: ["41474"],
                fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
                fc.TEST_RESULT: [verdict],
            }
            self.result.details["Additional_results"] = result_df

        except Exception as e:
            _log.error(f"Error processing signals: {e}")
            self.result.measured_result = DATA_NOK
            self.sig_sum = f"<p>Error processing signals : {e}</p>"
            plots.append(self.sig_sum)

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


@verifies("1493111")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_AnyPathFound",
    description="This testcase will verify if there is at least one reachable target pose "
    "(TargetPosesPort.targetPoses.reachableStatus == TP_FULLY_REACHABLE) for the given"
    " environmental model provided by ApParkingBoxPort and ApEnvModelPort, TRJPLA shall "
    "send TargetPosesPort.anyPathFound = true.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_0aH-EUM7Ee68PtCWeWkWbA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_p9KzlDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class TrjplaAnyPathFoundTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaAnyPathFound,
        ]


def convert_dict_to_pandas(
    signal_summary: dict,
    table_remark="",
    table_title="",
):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    # Create a DataFrame from the dictionary
    evaluation_summary = pd.DataFrame(
        {
            "Signal Summary": {key: key for key, val in signal_summary.items()},
            "Expected Values": {key: val[0] for key, val in signal_summary.items()},
            "Summary": {key: val[1] for key, val in signal_summary.items()},
            "Verdict": {key: val[2] for key, val in signal_summary.items()},
        }
    )

    # Generate HTML table using build_html_table function
    return fh.build_html_table(evaluation_summary, table_remark, table_title)


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r'D:\Rrec_Ext_Bsigs\Recordings\trjpla\exported_file__D2024_01_09_T13_51_40.bsig'

    # test_bsigs = r"D:\Rrec_Ext_Bsigs\Bsig_Output\carpc_wheelstopper\2022.08.04_at_13.29.33_svu-mi5_149.bsig"

    test_bsigs = r"D:\TAPOSD\ergfiles_foundposerate\currentPoseid\AUPSim_TestRun_ParallelLeftParking_2PB.erg"  # "D:\TAPOSD\MTS_Bsigs\2024.04.22_at_15.51.58_camera-mi_128\2024.04.22_at_15.51.58_camera-mi_128.bsig"

    debug(
        TrjplaAnyPathFoundTC,
        test_bsigs,
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
