#!/usr/bin/env python3
"""Defining  Bounding Box Subclass confidence cases"""
import logging
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import PathSpecification
from tsf.core.results import FALSE, NAN, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.CV.PCE.evaluation as eval
import pl_parking.PLP.CV.PCE.ft_helper as ft
import pl_parking.PLP.CV.PCE.ground_truth as label
import pl_parking.PLP.CV.PCE.simulation as sim
from pl_parking.PLP.CV.PCE.constants import BaseCtrl, PlotlyTemplate, SigStatus

TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "GRAPPA_SIGNALS"
ALIAS_JSON = "gt_data"

example_obj = ft.PCESignals()


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_PCE_BoundingBoxSubClassConfidence",
    description="This test step confirms that the component provides the subclass confidence of each and every detected"
    "Bounding Box.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ft.PCESignals)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=os.path.join(TSF_BASE, "data", "PCE_JSON_GT"),
        extension=".json",
    ),
)
class PCEBoundingBoxSubclassConfidenceTestStep(TestStep):
    """Test Step definition."""

    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        test_result = fc.INPUT_MISSING  # Result
        self.result.measured_result = NAN
        plot_titles, plots, remarks = fh.rep([], 3)

        reader = self.readers[SIGNAL_DATA]
        data = self.side_load[ALIAS_JSON]
        df = reader.as_plain_df
        check_cameras = ["fc", "rc", "rsc", "lsc"]
        signal_check = []
        for camera in check_cameras:
            # list the signals needed for test
            signal_check.append(f"Base_ctrl_opmode_{camera}")
            signal_check.append(f"detection_results_sig_status_{camera}")
            signal_check.append(f"num_bounding_box_detections_{camera}")
            signal_check.append(f"detection_results_timestamp_{camera}")
            for det in range(0, 64):
                for conf in range(0, 6):
                    signal_check.append((f"bounding_box_detections_subclass_confidence_of_{camera}_det_{det}", conf))
                # f'bounding_box_subclass_confidence_of_{camera}_det_' + str(det), conf
                for keypoint in range(0, 2):  # bounding box detections have 2 keypoints
                    signal_check.append(
                        f"bounding_box_detections_key_points_x_of_{camera}_det_{det}_keypoint_{keypoint}"
                    )
                    signal_check.append(
                        f"bounding_box_detections_key_points_y_of_{camera}_det_{det}_keypoint_{keypoint}"
                    )

        # checks availability of the signals
        signal_availability, list_of_missing_signals = ft.check_required_signals(signal_check, df)
        # Holds the timestamps and detection ID's for the associated detections
        availability_of_associated_detections = {}
        # Hold the Evaluation description for all the cameras
        evaluation_desc = {}
        # Holds the availability of bounding box detections in each camera
        bounding_detections = {}
        # set the ground truth frame.
        gf = label.GroundTruthFrame()
        # set the Simulation frame.
        sf = sim.SimulationFrame()
        # set the evaluation frame
        ef = eval.Evaluation()
        for camera in check_cameras:
            # # set all the associated detections for all the cameras
            # availability_of_associated_detections[camera] = False
            # Description to the evaluation
            evaluation_desc[camera] = f"Subclass of bounding box Detections in {camera.swapcase()}"
            # get labeled data for all the frames
            gf.get_data_from_label(data=data, camera=camera, class_type="BoundingBoxDetections")
            # get simulation/bsig data for all the frames
            sf.get_data_from_bsig(df=df, camera=camera, class_type="bounding_box_detections")
            # Check if there are bounding box detections available in both simulation and labeled data
            if bool(gf.gt_detections_timestamps[camera]) and bool(sf.bsig_detections_timestamps[camera]):
                # set the availablity of cuboid detections in each camera to True
                bounding_detections[camera] = True
                # get the valid timestamps and detections where there are associated detections found with labeled data
                ef.get_valid_timestamp_and_detections(gf, sf, camera, "bounding_box_detections")
                # Check whether there are associated bounding box detections available in simulation
                if bool(ef.valid_timestamps_in_camera[camera]):
                    # set to True when there are associated detections found in both bsig and labeled data
                    availability_of_associated_detections[camera] = True
                else:
                    # set to False when there are no associated detections found in both bsig and labeled data
                    availability_of_associated_detections[camera] = False
            else:
                # set the availablity of cuboid detections in each camera to False if there are no cuboid detections
                # available in simulation or labeled data
                bounding_detections[camera] = False
        eval_0 = (
            "Ensures that the component provides subclass confidence for all bounding box detections in each frame."
        )
        # captures the result of all cameras
        result_subclass_id = {}
        # captures the evaluation of all cameras
        evaluation_result = {}
        # Verdict result of all cameras
        verdict_result = {}
        # Holds the validity status of each detection keypoint
        dict_obj_keypoints = {}
        # Holds the status of validity of each detection keypoint
        dict_det_subclass_confidence = {}
        # check if all the required signals are available to test
        if signal_availability:
            for cam in check_cameras:
                # Check whether there are cuboid detections available in recording and/or GT
                if bounding_detections[cam] is True:
                    # Check whether there are associated cuboid detections found in recording and/or GT
                    if availability_of_associated_detections[cam] is True:

                        # Filters df for 'detection_results_sig_status == SigStatus.AL_SIG_STATE_OK' and
                        # 'num_bounding_box_detections is !=0'
                        df_filtered_specific_columns = df[
                            (df[f"Base_ctrl_opmode_{cam}"] == BaseCtrl.GS_BASE_OM_RUN)
                            & (df[f"detection_results_sig_status_{cam}"] == SigStatus.AL_SIG_STATE_OK)
                            & (df[f"num_bounding_box_detections_{cam}"] != 0)
                        ]
                        # remove the duplicate timestamps.
                        df_filtered = df_filtered_specific_columns.drop_duplicates(
                            subset=[f"detection_results_timestamp_{cam}"], keep="last"
                        )
                        # checks whether the keypoint of each valid detection is > 0
                        validity_of_keypoints, invalid_keypoints_timestamps, dict_obj_keypoints[cam] = (
                            ft.check_validity_of_bounding_box_keypoints(df_filtered, cam, ef)
                        )
                        if validity_of_keypoints and not df_filtered.empty:
                            # performs following when keypoints are valid, 'Detection_Results_sigstatus == \
                            # SigStatus.AL_SIG_STATE_OK' and 'num_bounding_box_detections is !=0'

                            # checks whether the subclass_confidence lies in range of 0 to 1
                            (
                                valid_subclass_confidence,
                                invalid_subclass_conf_timestamps,
                                dict_det_subclass_confidence[cam],
                            ) = ft.check_bounding_box_subclass_confidence(
                                df_filtered, cam, ef, dict_obj_keypoints[cam], "subclass_conf"
                            )
                            if valid_subclass_confidence:
                                # sets test to Pass when subclass confidence of each detected bounding box lies in between 0 and 1
                                result_subclass_id[cam] = True
                                evaluation_result[cam] = (
                                    f"subclass confidence of each {cam.swapcase()} detected bounding box lies in between 0 and 1"
                                )
                                verdict_result[cam] = "passed"
                            else:
                                # sets test to Fail when subclass confidence of each detected bounding box does not lies in
                                # between 0 and 1
                                result_subclass_id[cam] = False
                                evaluation_result[cam] = (
                                    f"subclass confidence of each {cam.swapcase()} detected bounding box does not lies in between 0 and 1"
                                )
                                verdict_result[cam] = "failed"
                        else:
                            # when keypoint is not as expected
                            result_subclass_id[cam] = fc.NOT_ASSESSED
                            evaluation_result[cam] = (
                                f"precondition not met at the timestamps: {invalid_keypoints_timestamps}"
                            )
                            verdict_result[cam] = "Not assessed"
                    else:
                        result_subclass_id[cam] = fc.NOT_ASSESSED
                        evaluation_result[cam] = "No associated bounding box detections are available in SIM"
                        verdict_result[cam] = "Not assessed"
                else:
                    result_subclass_id[cam] = fc.NOT_ASSESSED
                    evaluation_result[cam] = "No Bounding box detections are available in GT and/or SIM"
                    verdict_result[cam] = "Not assessed"
            if all(ele is True for ele in result_subclass_id.values()):
                # perform following when most confident subclass is provided for all of the bounding detections.
                test_result = fc.PASS
                self.result.measured_result = TRUE
                self.result.details["Step_result"] = test_result
            elif any(ele is False for ele in result_subclass_id.values()):
                # perform following when most confident subclass is not provided for any of the bounding detections.
                test_result = fc.FAIL
                self.result.measured_result = FALSE
                self.result.details["Step_result"] = test_result
            else:
                # perform following when precondition is not met for any camera instance
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = NAN
                self.result.details["Step_result"] = test_result
            # Set table dataframe
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": evaluation_desc.values(),
                    "Result": evaluation_result.values(),
                    "Verdict": verdict_result.values(),
                }
            )
            # Add the table
            sig_sum = fh.build_html_table(signal_summary)
            # signal plot
            plot_titles.append("")
            plots.append(sig_sum)
            remarks.append("")
        else:
            # Set table dataframe
            evaluation_text = (
                f"Evaluation is {test_result}, Input signals {list_of_missing_signals} are not available in bsig file."
            )
            signal_summary = pd.DataFrame(
                {
                    "Evaluation": {
                        "1": eval_0,
                    },
                    "Result": {
                        "1": evaluation_text,
                    },
                    "Verdict": {
                        "1": test_result,
                    },
                }
            )
            # Add the table
            sig_sum = fh.build_html_table(signal_summary)
            plots.append(sig_sum)
        # plotting the signals needed
        num_of_valid_det_cam = {}
        for camera in check_cameras:
            num_of_valid_det_cam[camera] = False

            if (
                bounding_detections[camera] is True
                and availability_of_associated_detections[camera]
                and bool(ef.valid_timestamps_in_camera[camera])
            ):
                df_filtered_specific_columns = df[
                    (df[f"Base_ctrl_opmode_{camera}"] == BaseCtrl.GS_BASE_OM_RUN)
                    & (df[f"detection_results_sig_status_{camera}"] == SigStatus.AL_SIG_STATE_OK)
                    & (df[f"num_bounding_box_detections_{camera}"] != 0)
                ]
                df_filtered = df_filtered_specific_columns.drop_duplicates(
                    subset=[f"detection_results_timestamp_{camera}"], keep="last"
                )
                if not df_filtered.empty:
                    fig_bounding_box_subclass_conf = go.Figure()
                    fig_num_of_detections_sig_status = go.Figure()
                    fig_keypoints = go.Figure()

                    x_arr = np.arange(2)
                    x_arr_sub = np.arange(3)
                    num_of_valid_det = {}

                    for _, row in df_filtered.iterrows():
                        valid_detection = 0
                        timestamps = int(row[f"detection_results_timestamp_{camera}"])
                        num_bounding_box_detections = int(row[f"num_bounding_box_detections_{camera}"])
                        if timestamps in ef.valid_timestamps_in_camera[camera]:
                            for det in range(0, num_bounding_box_detections):
                                # used to plot the subclass of each valid detection
                                list_subclass_conf = []
                                # used to plot the keypointx of each valid detection
                                list_keypoints_x = []
                                # used to plot the keypointy of each valid detection
                                list_keypoints_y = []
                                if (ef.valid_detections_in_camera[camera][f"{timestamps}_{det}"]) is True:
                                    if (
                                        dict_obj_keypoints[camera][f"frame{timestamps}_det{det}"] is True
                                        and dict_det_subclass_confidence[camera][f"frame{timestamps}_det{det}"] is True
                                    ):
                                        valid_detection = valid_detection + 1
                                        for conf in range(0, 2):
                                            list_keypoints_x.append(
                                                row[
                                                    f"bounding_box_detections_key_points_x_of_{camera}_det_{det}_keypoint_{conf}"
                                                ]
                                            )
                                            list_keypoints_y.append(
                                                row[
                                                    f"bounding_box_detections_key_points_y_of_{camera}_det_{det}_keypoint_{conf}"
                                                ]
                                            )
                                        for conf in range(0, 6):
                                            list_subclass_conf.append(
                                                row[
                                                    f"bounding_box_detections_subclass_confidence_of_{camera}_det_{det}",
                                                    conf,
                                                ]
                                            )

                                        # adding the subclass confidence of each detection to the figure
                                        fig_bounding_box_subclass_conf.add_trace(
                                            go.Scatter(
                                                x=x_arr_sub,
                                                y=np.array(list_subclass_conf),
                                                mode="lines+markers",
                                                name=f"OD_timestamp_{timestamps}_Bbox[{det}].subclassconfidence",
                                            )
                                        )
                                        # adding the keypoints of each detection to the figure
                                        fig_keypoints.add_trace(
                                            go.Scatter(
                                                x=x_arr,
                                                y=np.array(list_keypoints_x),
                                                mode="lines+markers",
                                                name=f"OD_timestamp_{timestamps}_Bbox[{det}].keypointX",
                                            )
                                        )
                                        fig_keypoints.add_trace(
                                            go.Scatter(
                                                x=x_arr,
                                                y=np.array(list_keypoints_y),
                                                mode="lines+markers",
                                                name=f"OD_timestamp_{timestamps}_Bbox[{det}].keypointy",
                                            )
                                        )
                                if valid_detection > 0:
                                    num_of_valid_det[timestamps] = valid_detection
                                    num_of_valid_det_cam[camera] = True

                    df_graph = pd.DataFrame()
                    df_graph["keys"] = list(num_of_valid_det.keys())
                    df_graph["values"] = list(num_of_valid_det.values())
                    # adding the number of valid bounding box detections in each frame to the figure
                    fig_num_of_detections_sig_status.add_trace(
                        go.Scatter(
                            x=df_graph["keys"],
                            y=df_graph["values"],
                            mode="lines+markers",
                            name="num_of_valid_bounding_box_detections",
                        )
                    )

                fig_bounding_box_subclass_conf.layout = go.Layout(
                    yaxis=dict(tickformat="14"),
                    xaxis=dict(tickformat="14"),
                    xaxis_title=f"{camera.swapcase()}_bounding_box_subclass confidence",
                    yaxis_title="SubclassConfidence",
                    title=f"{camera.swapcase()} Valid Bounding Box detections Subclass Confidence",
                )
                fig_num_of_detections_sig_status.layout = go.Layout(
                    yaxis=dict(tickformat="14"),
                    xaxis=dict(tickformat="14"),
                    xaxis_title=f"{camera.swapcase()}_OD Timestamps(us)",
                    yaxis_title="Valid detections",
                    title=f"{camera.swapcase()} Number of valid bounding box detections in each frame",
                )
                fig_keypoints.layout = go.Layout(
                    yaxis=dict(tickformat="14"),
                    xaxis=dict(tickformat="14"),
                    xaxis_title=f"{camera.swapcase()}Bounding Box Keypoints",
                    yaxis_title="Keypoint values",
                    title=f"{camera.swapcase()} Valid Bounding Box detections Keypoints",
                )

                if num_of_valid_det_cam[camera] is True:
                    # adding the number of valid bounding box detections in each frame to the plot
                    plots.append(fig_num_of_detections_sig_status)
                    # adding the subclass confidence of each detection to the plot
                    plots.append(fig_bounding_box_subclass_conf)
                    # adding the keypoints of each detection to the plot
                    plots.append(fig_keypoints)

                    fig_num_of_detections_sig_status.update_layout(PlotlyTemplate.lgt_tmplt, showlegend=True)
                    fig_bounding_box_subclass_conf.update_layout(PlotlyTemplate.lgt_tmplt, showlegend=True)
                    fig_keypoints.update_layout(PlotlyTemplate.lgt_tmplt, showlegend=True)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1568166"],
            fc.TESTCASE_ID: ["61468"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Ensures that the component provides confidence information of every subclass for every detected "
                "bounding box."
            ],
            fc.TEST_RESULT: [test_result],
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

        self.result.details["Additional_results"] = result_df


@verifies("L3_PCE_1568166")
@testcase_definition(
    name="SWRT_CNC_PCE_BoundingBoxSubClassConfidence",
    description="This test ensures that the bounding box subclass confidence lies in range of 0 to 1",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class PCEBoundingBoxSubclassConfidence(TestCase):
    """ListofParkingMarkings test case."""

    custom_report = fh.MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            PCEBoundingBoxSubclassConfidenceTestStep,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.
    """
    test_bsigs = (
        r"D:\csv's\check_nextvisu\2024.12.04_at_14.23.36_camera-mi_9056\2024.12.04_at_14.23.36_camera-mi_9056.bsig"
    )
    debug(
        PCEBoundingBoxSubclassConfidence,
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
