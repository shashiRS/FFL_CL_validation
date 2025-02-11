"""SWRT CNC TRAJPLA TestCases"""

import logging
import os

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

SIGNAL_DATA = "MF_TP_NOT_FOUND"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Target pose not found",
    description="TRJPLA shall not provide any target pose or parking path based on input conditions  of apState, gpState, rmState, raState and mpState.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TrjplaTargetPoseNotFound(TestStep):
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
        try:
            evaluation = ""
            signals = self.readers[SIGNAL_DATA]
            # plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)
            signal_summary = {}
            signal_name = example_obj._properties

            ap_state = signals["ApState"]
            mp_state = signals["MpState"]
            ra_state = signals["RaState"]
            gp_state = signals["GpState"]
            rm_state = signals["RmState"]
            num_valid_poses = signals["numValidPoses"]
            traj_valid_nu = signals["trajValid_nu"]
            num_valid_ctrlpoints_nu = signals["numValidCtrlPoints_nu"]

            num_valid_poses_nu = signals["numValidPoses_nu"]
            num_valid_segments = signals["numValidSegments"]
            anypath_found = signals["anyPathFound"]

            signals["ApState"] = ap_state.apply(lambda x: fh.get_status_label(x, trajpla.ApStates))
            signals["MpState"] = mp_state.apply(lambda x: fh.get_status_label(x, trajpla.MpStates))
            signals["RaState"] = ra_state.apply(lambda x: fh.get_status_label(x, trajpla.RaStates))
            signals["GpState"] = gp_state.apply(lambda x: fh.get_status_label(x, trajpla.GpStates))
            signals["RmState"] = rm_state.apply(lambda x: fh.get_status_label(x, trajpla.RmStates))

            eval_cond = None
            for idx in range(0, len(ap_state)):
                if (
                    ap_state.iloc[idx] == trajpla.ApStates.AP_INACTIVE
                    and mp_state.iloc[idx] == trajpla.MpStates.MP_INACTIVE
                    and ra_state.iloc[idx] == trajpla.RaStates.RA_INACTIVE
                    and gp_state.iloc[idx] == trajpla.GpStates.GP_INACTIVE
                    and rm_state.iloc[idx] == trajpla.RmStates.RM_INACTIVE
                ) or (
                    ap_state.iloc[idx] == trajpla.ApStates.AP_AVG_FINISHED
                    or mp_state.iloc[idx] == trajpla.MpStates.MP_TRAIN_FINISHED
                    or mp_state.iloc[idx] == trajpla.MpStates.MP_RECALL_FINISHED
                    or ra_state.iloc[idx] == trajpla.RaStates.RA_AVG_FINISHED
                    or gp_state.iloc[idx] == trajpla.GpStates.GP_AVG_FINISHED
                    or rm_state.iloc[idx] == trajpla.RmStates.RM_AVG_FINISHED
                ):

                    if (
                        num_valid_poses.iloc[idx] == 0
                        and traj_valid_nu.iloc[idx] == 0
                        and num_valid_ctrlpoints_nu.iloc[idx] == 0
                        and num_valid_poses_nu.iloc[idx] == 0
                        and num_valid_segments.iloc[idx] == 0
                        and anypath_found.iloc[idx] == 0
                    ):
                        evaluation = "Passed"
                        eval_cond = True
                    else:
                        evaluation = " ".join(
                            f"The evaluation of {signal_name['numValidPoses']} and "
                            f"{signal_name['trajValid_nu']} and {signal_name['numValidCtrlPoints_nu']} and "
                            f"{signal_name['numValidPoses_nu']} and {signal_name['numValidSegments']} and "
                            f"{signal_name['anyPathFound']} is "
                            f"FAILED at frame {idx}".split()
                        )
                        eval_cond = False
                        break

            if evaluation == "":
                evaluation = " ".join("Input conditions was never met").split()
                eval_cond = False

            if eval_cond:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            verdict = "passed" if eval_cond else "failed" if eval_cond is False else "not assessed"
            expected_val = "AP..targetPosesPort.numValidPoses == 0 </br>\
              AP.plannedTrajPort.trajValid_nu == 0 </br>\
              AP.planningCtrlPort.plannedTrajPort.numValidCtrlPoints_nu == 0 </br>\
              trjplaVisuPort.numValidPoses_nu == 0 </br>\
              AP.TrajPlanVisuPort.numValidSegments == 0 </br>\
              AP.targetPosesPort.anyPathFound == 0 </br>"

            signal_summary[
                f"{signal_name['ApState']} == AP_INACTIVE(0) or AP_AVG_FINISHED(8) <br>"
                f"{signal_name['GpState']} == GP_INACTIVE(0) or GP_AVG_FINISHED(7) <br>"
                f"{signal_name['MpState']} == MP_INACTIVE(0) or MP_TRAIN_FINISHED(5) or MP_RECALL_FINISHED(9) <br>"
                f"{signal_name['RmState']} == RM_INACTIVE(0) or RM_AVG_FINISHED(4) <br>"
                f"{signal_name['RaState']} == RA_INACTIVE(0) or RA_AVG_FINISHED(4)"
            ] = [expected_val, evaluation, verdict]

            remark = " ".join(
                f" {signal_name['numValidPoses']} = 0 and {signal_name['trajValid_nu']} = 0 and <br> "
                f"{signal_name['numValidCtrlPoints_nu']} = 0 and {signal_name['numValidPoses_nu']} = 0 and <br>"
                f" {signal_name['numValidSegments']} = 0 and <br> {signal_name['anyPathFound']} = 0".split()
            )
            # The signal summary and observations will be converted to pandas and finally the html table will be created with them
            self.sig_sum = convert_dict_to_pandas(signal_summary, remark)
            plots.append(self.sig_sum)

            frame_number_list = list(range(0, len(ap_state)))
            fig = go.Figure()
            # add the needed signals in the plot
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=ap_state,
                    mode="lines",
                    name=signal_name["ApState"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["ApState"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=mp_state,
                    mode="lines",
                    name=signal_name["MpState"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["MpState"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=gp_state,
                    mode="lines",
                    name=signal_name["GpState"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["GpState"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=ra_state,
                    mode="lines",
                    name=signal_name["RaState"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["RaState"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=rm_state,
                    mode="lines",
                    name=signal_name["RmState"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br>Status: %{text}<extra></extra>",
                    text=signals["RmState"],
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=traj_valid_nu,
                    mode="lines",
                    name=signal_name["trajValid_nu"],
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
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=num_valid_poses_nu,
                    mode="lines",
                    name=signal_name["numValidPoses_nu"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=num_valid_segments,
                    mode="lines",
                    name=signal_name["numValidSegments"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=num_valid_ctrlpoints_nu,
                    mode="lines",
                    name=signal_name["numValidCtrlPoints_nu"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=frame_number_list,
                    y=anypath_found,
                    mode="lines",
                    name=signal_name["anyPathFound"],
                    hovertemplate="Frame: %{x}<br>Value: %{y}<br><extra></extra>",
                )
            )
            fig.layout = go.Layout(
                yaxis=dict(tickformat="14"),
                xaxis=dict(tickformat="14"),
                xaxis_title="Frames",
                title="Graphical Overview of Evaluated signals",
            )
            fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plots.append(fig)

            result_df = {
                "Verdict": {"value": verdict, "color": fh.get_color(verdict)},
                fc.REQ_ID: ["1492142"],
                fc.TESTCASE_ID: ["41474"],
                fc.TEST_SAFETY_RELEVANT: [fc.SAFETY_RELEVANT_QM],
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


@verifies("1492142")
@testcase_definition(
    name="SWRT_CNC_TRJPLA_TargetPoseNotFound",
    description="This testcase verifies that, if all conditions below are fulfilled:"
    "<br>SlotCtrlPort.planningCtrlPort.apState == AP_INACTIVE"
    "<br>SlotCtrlPort.planningCtrlPort.gpState == GP_INACTIVE"
    "<br>SlotCtrlPort.planningCtrlPort.rmState == RM_INACTIVE"
    "<br>SlotCtrlPort.planningCtrlPort.raState == RA_INACTIVE"
    "<br>SlotCtrlPort.planningCtrlPort.mpState == MP_INACTIVE"
    "<br>or one condition below is fulfilled:"
    "<br>SlotCtrlPort.planningCtrlPort.apState == AP_AVG_FINISHED"
    "<br>SlotCtrlPort.planningCtrlPort.gpState == GP_AVG_FINISHED"
    "<br>SlotCtrlPort.planningCtrlPort.rmState == RM_AVG_FINISHED"
    "<br>SlotCtrlPort.planningCtrlPort.raState == RA_AVG_FINISHED"
    "<br>SlotCtrlPort.planningCtrlPort.mpState == MP_RECALL_FINISHED"
    "<br>SlotCtrlPort.planningCtrlPort.mpState == MP_TRAIN_FINISHED,"
    "<br>TRJPLA does not provide any target pose or parking path.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_EbB5IEJ8Ee68PtCWeWkWbA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_p9KzlDK_Ee6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class TrjplaTargetPoseNotFoundTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            TrjplaTargetPoseNotFound,
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
