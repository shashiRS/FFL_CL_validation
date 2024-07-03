"""Parking marker test cases"""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "..", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


import typing

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.common import PathSpecification
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import CemSignals, CustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants, ConstantsCem, ConstantsCemInput, GroundTruthCem
from pl_parking.PLP.CEM.ft_erg_helper import ErgPlots, TranslationRotation
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper
from pl_parking.PLP.CEM.ground_truth.kml_parser import CemGroundTruthHelper
from pl_parking.PLP.CEM.inputs.input_CemErgReader import ErgPmReader
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PCLDelimiter, PclDelimiterReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader
from pl_parking.PLP.CEM.inputs.input_DGPSReader import DGPSReader
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera, PMDReader

SIGNAL_DATA = "CEM_PFS_PCL_Accuracy"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL False Positive",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLFalsePositive(TestStep):
    """TestStep for evaluating False Positive cases in PCL, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        dgps_buffer = DGPSReader(reader).convert_to_class()
        cem_ground_truth_utm = CemGroundTruthHelper.get_cem_ground_truth_from_files_list(
            [os.path.dirname(__file__) + "\\" + f_path for f_path in GroundTruthCem.kml_files]
        )
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        pmd_data = PMDReader(reader).convert_to_class()

        number_associated_pcl: typing.List[typing.Tuple[int, int]] = []
        pcl_false_positive_list: typing.List[float] = []
        for _, pcl_timeframe in enumerate(pcl_data):
            dgps_pose = dgps_buffer.estimate_vehicle_pose(pcl_timeframe.timestamp)
            timeframe_nbr_associated_lines = 0
            if dgps_pose is not None and len(pcl_timeframe.pcl_delimiter_array) > 0:
                false_positive = FtPclHelper.calculate_cem_pcl_false_positive_utm(
                    dgps_pose,
                    pcl_timeframe.pcl_delimiter_array,
                    cem_ground_truth_utm.parking_markers,
                    AssociationConstants.PCL_ASSOCIATION_RADIUS,
                )
                timeframe_nbr_associated_lines = len(pcl_timeframe.pcl_delimiter_array) - false_positive * len(
                    pcl_timeframe.pcl_delimiter_array
                )

                pcl_false_positive_list.append(false_positive)

            number_associated_pcl.append((pcl_timeframe.timestamp, timeframe_nbr_associated_lines))

        pmd_false_positive_list: typing.List[float] = []
        pmd_false_positive_per_camera: typing.Dict[PMDCamera, typing.List[float]] = dict()
        pmd_number_associated_lines: typing.Dict[PMDCamera, typing.List[typing.Tuple[int, int]]] = dict()
        for camera, timeframe_list in pmd_data.items():
            pmd_false_positive_per_camera[camera] = []
            pmd_number_associated_lines[camera] = []
            for pmd_timeframe in timeframe_list:
                dgps_pose = dgps_buffer.estimate_vehicle_pose(pmd_timeframe.timestamp)
                timeframe_nbr_associated_lines = 0
                if dgps_pose is not None and len(pmd_timeframe.pmd_lines) > 0:
                    false_positive = FtPclHelper.calculate_pmd_false_positive_utm(
                        dgps_pose,
                        pmd_timeframe.pmd_lines,
                        cem_ground_truth_utm.parking_markers,
                        AssociationConstants.PCL_ASSOCIATION_RADIUS,
                    )
                    timeframe_nbr_associated_lines = len(pmd_timeframe.pmd_lines) - false_positive * len(
                        pmd_timeframe.pmd_lines
                    )

                    pmd_false_positive_list.append(false_positive)
                    pmd_false_positive_per_camera[camera].append(false_positive)

                pmd_number_associated_lines[camera].append((pmd_timeframe.timestamp, timeframe_nbr_associated_lines))

        avg_pcl_false_positive = np.mean(pcl_false_positive_list)
        avg_pmd_false_positive = np.mean(pmd_false_positive_list)

        if avg_pmd_false_positive >= avg_pcl_false_positive:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        # Average False Positive ration table
        source_false_positive = ["CEM", "PMD", "PMD Front", "PMD Rear", "PMD Right", "PMD Left"]
        values_false_positive = [
            avg_pcl_false_positive,
            avg_pmd_false_positive,
            np.mean(pmd_false_positive_per_camera[PMDCamera.FRONT]),
            np.mean(pmd_false_positive_per_camera[PMDCamera.REAR]),
            np.mean(pmd_false_positive_per_camera[PMDCamera.RIGHT]),
            np.mean(pmd_false_positive_per_camera[PMDCamera.LEFT]),
        ]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Source", "Average False Positive"]),
                    cells=dict(values=[source_false_positive, values_false_positive]),
                )
            ]
        )
        plot_titles.append("Average False Positive rate for parking markers")
        plots.append(fig)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[timeframe.timestamp for timeframe in pcl_data],
                y=[len(timeframe.pcl_delimiter_array) for timeframe in pcl_data],
                mode="lines",
                name="Number of CEM PCL",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[timestamp for timestamp, _ in number_associated_pcl],
                y=[nbr_associated for _, nbr_associated in number_associated_pcl],
                mode="lines",
                name="Number of associated CEM PCL to the ground truth",
            )
        )
        plot_titles.append("Number of CEM PCL")
        plots.append(fig)
        remarks.append("")

        for camera, timeframe_list in pmd_data.items():
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=[timeframe.timestamp for timeframe in timeframe_list],
                    y=[len(timeframe.pmd_lines) for timeframe in timeframe_list],
                    mode="lines",
                    name=f"{camera._name_} camera number of PMD",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[timestamp for timestamp, _ in pmd_number_associated_lines[camera]],
                    y=[nbr_associated for _, nbr_associated in pmd_number_associated_lines[camera]],
                    mode="lines",
                    name=f"{camera._name_} camera number of associated PMD to the ground truth",
                )
            )
            plot_titles.append(f"{camera._name_} camera number of PMD")
            plots.append(fig)
            remarks.append("")

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM PFS PCL False Positive",
    description="The test passes if the false positive ratio of the PMD lines is less or"
    "equal to the false positive ratio of the PCL lines.",
)
class FtPCLFalsePositive(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLFalsePositive]


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Field of View",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLFieldOfView(TestStep):
    """TestStep for assessing Field of View in PCL, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        input_reader = PclDelimiterReader(reader)
        delimiter_data = input_reader.convert_to_class()

        data_df = input_reader.data.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        if ConstantsCemInput.PCLEnum in pcl_type.values:
            rows = []
            failed = 0
            for time_frame in delimiter_data:
                for PCL in time_frame.pcl_delimiter_array:
                    closes_point = FtPclHelper.get_closest_point(PCL)
                    if (
                        abs(closes_point.x) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
                        or abs(closes_point.y) > ConstantsCem.AP_G_DES_MAP_RANGE_M / 2
                    ):
                        failed += 1
                        values = [
                            [time_frame.timestamp],
                            [PCL.delimiter_id],
                            [closes_point.x],
                            [closes_point.y],
                            [ConstantsCem.AP_G_DES_MAP_RANGE_M],
                        ]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                header = ["Timestamp", "DelimiterID", "x", "y", "LIMIT_OUTPUT_FIELD_OF_VIEW"]
                fig = go.Figure(data=[go.Table(header=dict(values=header), cells=dict(values=values))])
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM PFS PCL Field of View",
    description="This test case checks if CEM's output contains only parking markers inside the limited field of view.",
)
class FtPCLFieldOfView(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLFieldOfView]


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Furthest Line",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLFurthestLineDeleted(TestStep):
    """TestStep for detecting the furthest deleted line in PCL, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        reader = self.readers[SIGNAL_DATA].signals
        inputReader = PclDelimiterReader(reader)
        vedodo_buffer = VedodoReader(reader).convert_to_class()
        delimiterData = inputReader.convert_to_class()
        nbrTimeframes = len(delimiterData)

        data_df = inputReader.data.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        if ConstantsCemInput.PCLEnum in pcl_type.values:
            failed = 0
            for i in range(nbrTimeframes - 1):
                prevTimeframe = delimiterData[i]
                curTimeframe = delimiterData[i + 1]

                relative_motion = vedodo_buffer.calc_relative_motion(prevTimeframe.timestamp, curTimeframe.timestamp)

                missingPcls: typing.List[PCLDelimiter] = []

                if len(prevTimeframe.pcl_delimiter_array) > 0 and len(curTimeframe.pcl_delimiter_array) > 0:
                    if len(curTimeframe.pcl_delimiter_array) == ConstantsCem.PCL_MAX_NUM_MARKERS:
                        missingPcls = FtPclHelper.find_missing_pcl_line_ids(prevTimeframe, curTimeframe)

                if len(missingPcls) > 0:
                    _, furthestPclDistance = FtPclHelper.get_furthest_line(curTimeframe)

                    for missingLine in missingPcls:
                        transformed_line = FtPclHelper.transform_pcl(missingLine, relative_motion)
                        if FtPclHelper.distance_pcl_vehicle(transformed_line) < furthestPclDistance:
                            failed += 1

            if failed:
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Number of failed deleted markers"]), cells=dict(values=[[failed]])
                        )
                    ]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM PFS PCL Furthest Line",
    description="In case the mentioned limit is reached, the furthest parking marking shall be deleted",
)
class FtPCLFurthestLineDeleted(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLFurthestLineDeleted]


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL ID Maintenance",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLMaintID(TestStep):
    """TestStep for maintaining ID in PCL, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        pcl_reader = PclDelimiterReader(reader)
        pcl_data = pcl_reader.convert_to_class()
        pmd_data = PMDReader(reader).convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()

        data_df = pcl_reader.data.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        if ConstantsCemInput.PCLEnum in pcl_type.values:
            rows = []
            failed = 0
            for index, curTimeframe in enumerate(pcl_data):
                if index == 0:
                    continue
                prevTimeframe = pcl_data[index - 1]
                relative_motion_output = vedodo_buffer.calc_relative_motion(
                    curTimeframe.timestamp, prevTimeframe.timestamp
                )

                transformed_prev_marker = [
                    FtPclHelper.transform_pcl(marker, relative_motion_output)
                    for marker in prevTimeframe.pcl_delimiter_array
                ]

                psd_timeframe_index = [
                    FtPclHelper.get_PMD_timeframe_index(
                        curTimeframe.timestamp, prevTimeframe.timestamp, pmd_data[camera]
                    )
                    for camera in PMDCamera
                ]

                psd_timeframes = [
                    pmd_data[camera][psd_timeframe_index[int(camera)]]
                    for camera in PMDCamera
                    if psd_timeframe_index[int(camera)] is not None
                ]

                updatedMarkers = FtPclHelper.get_marker_with_associated_input(
                    transformed_prev_marker, psd_timeframes, AssociationConstants.PCL_ASSOCIATION_RADIUS
                )

                associations = FtPclHelper.associate_PCL_list(
                    curTimeframe.pcl_delimiter_array, updatedMarkers, AssociationConstants.PCL_ASSOCIATION_RADIUS
                )

                for prev_ixd, curr_index in associations.items():
                    if (
                        updatedMarkers[prev_ixd].delimiter_id
                        != curTimeframe.pcl_delimiter_array[curr_index].delimiter_id
                    ):
                        failed += 1
                        values = [
                            [curTimeframe.timestamp],
                            [updatedMarkers[prev_ixd].delimiter_id],
                            [curTimeframe.pcl_delimiter_array[curr_index].delimiter_id],
                        ]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Timestamp", "Prev Slot ID", "Curr Slot ID"]), cells=dict(values=values)
                        )
                    ]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM PFS PCL ID Maintenance",
    description="This test checks that EnvironmentFusion maintains the identifier of each parking marker"
    "if a parking marker detection is received in the current timeframe and can be associated"
    "to a parking marker already received in previous time frames.",
)
class FtPCLMaintID(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLMaintID]


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Number Limit",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLNumberLimit(TestStep):
    """TestStep for assessing the number limit in PCL, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        inputReader = PclDelimiterReader(reader)
        delimiterData = inputReader.convert_to_class()

        test_result = fc.PASS
        for timeframe in delimiterData:
            if len(timeframe.pcl_delimiter_array) > ConstantsCem.PCL_MAX_NUM_MARKERS:
                test_result = fc.FAIL
                break

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM PFS PCL Number Limit",
    description=f"""Limit the number of PCL to {ConstantsCem.PCL_MAX_NUM_MARKERS}""",
)
class FtPCLNumberLimit(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLNumberLimit]


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Unique ID",
    description="This test checks that CEM provides an identifier for each parking marker, "
    "and the identifier is unique in each timeframe.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLUniqueID(TestStep):
    """TestStep for ensuring unique ID in PCL, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        input_reader = PclDelimiterReader(reader)
        delimiter_data = input_reader.convert_to_class()

        data_df = input_reader.data.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        if ConstantsCemInput.PCLEnum in pcl_type.values:
            rows = []
            failed = 0
            for time_frame in delimiter_data:
                ids = []
                for PCL in time_frame.pcl_delimiter_array:
                    if PCL.delimiter_id in ids:
                        failed += 1
                        values = [[time_frame.timestamp], [PCL.delimiter_id]]
                        rows.append(values)
                    else:
                        ids.append(PCL.delimiter_id)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[go.Table(header=dict(values=["Timestamp", "DelimiterID"]), cells=dict(values=values))]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM PFS PCL Unique ID",
    description="This test checks that CEM provides an identifier for each parking marker, and the identifier is "
    "unique in each timeframe.",
)
class FtPCLUniqueID(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLUniqueID]


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Precision Rate",
    description="This KPI provides the average precision rate of the PCL lines in the CEM output,\
         Precision = TP / ( TP + FP)",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
@register_side_load(
    alias="JsonGt",
    side_load=JsonSideLoad,  # type of side loaders
    path_spec=PathSpecification(
        folder=os.path.join(TSF_BASE, "data", "CEM_json_gt"),
        extension=".json",
    ),
    # Absolute path for the sideload.
)
class TestStepKpiPCLPrecisionRate(TestStep):
    """TestStep for measuring Precision Rate in PCL, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        pcl_output_reader = PclDelimiterReader(reader)
        pcl_data = pcl_output_reader.convert_to_class()
        ego_position = pd.DataFrame()

        # Load GT data
        if pcl_output_reader.synthetic_flag:
            pm_gt = ErgPmReader(reader)
            pm_gt_array = pm_gt.convert_to_class()
            # Load signals
            ego_position["timestamp"] = reader.as_plain_df["numPclDelimiters_timestamp"]
            ego_position["Fr1_x"] = reader.as_plain_df["Fr1_x"]
            ego_position["Fr1_y"] = reader.as_plain_df["Fr1_y"]
            ego_position["yaw"] = reader.as_plain_df["synthetic_yaw"]
            ego_position = ego_position[(ego_position.timestamp != 0)]
            ego_position = ego_position.drop_duplicates(subset="timestamp")
            fig = ErgPlots.plot_pcl_output_gt(pcl_output_reader.data.as_plain_df, pm_gt.data, ego_position)
            plot_titles.append("GT and PCL output animation")
            plots.append(fig)
            remarks.append("")
            fig1 = ErgPlots().plot_ego_pcl_gt(ego_position, pm_gt.data)
            plot_titles.append("Ego trajectory and GT")
            plots.append(fig1)
            remarks.append("")

        else:
            gt_data = self.side_load["JsonGt"]
            park_marker_gt = FtPclHelper.get_pcl_from_json_gt(gt_data)

        number_associated_pcl: typing.List[typing.Tuple[int, int]] = []
        pcl_precision_list: typing.List[float] = []
        for _, pcl_timeframe in enumerate(pcl_data):
            if pcl_output_reader.synthetic_flag:
                pose = ego_position.loc[ego_position["timestamp"] == pcl_timeframe.timestamp, ["Fr1_x", "Fr1_y", "yaw"]]
            else:
                gt_with_closest_timestamp = park_marker_gt.get(
                    min(park_marker_gt.keys(), key=lambda k: abs(k - pcl_timeframe.timestamp))
                )
            timeframe_nbr_associated_lines = 0
            if len(pcl_timeframe.pcl_delimiter_array) > 0:
                if pcl_output_reader.synthetic_flag:
                    if not pose.empty:
                        # Compute GT PM position with respect to ego
                        pcl_array_gt = TranslationRotation().update_position(
                            pm_gt_array[0], [pose["Fr1_x"].values[0], pose["Fr1_y"].values[0]], pose["yaw"].values[0]
                        )
                        precision = FtPclHelper.calculate_cem_pcl_precision_iso(
                            pcl_timeframe.pcl_delimiter_array, pcl_array_gt, AssociationConstants.PCL_ASSOCIATION_RADIUS
                        )
                elif not pcl_output_reader.synthetic_flag:
                    precision = FtPclHelper.calculate_cem_pcl_precision_iso(
                        pcl_timeframe.pcl_delimiter_array,
                        gt_with_closest_timestamp,
                        AssociationConstants.PCL_ASSOCIATION_RADIUS,
                    )
                else:
                    continue
                timeframe_nbr_associated_lines = precision * len(pcl_timeframe.pcl_delimiter_array)

                pcl_precision_list.append(precision * 100)

            number_associated_pcl.append((pcl_timeframe.timestamp, timeframe_nbr_associated_lines))

        avg_pcl_precision_rate = np.mean(pcl_precision_list)

        if avg_pcl_precision_rate >= ConstantsCem.PCL_PRECISION_RATE:
            test_result = fc.PASS
        else:
            test_result = fc.FAIL

        # Average Precision Rate ration table
        source_precision_rate = ["CEM"]
        values_precision_rate = [avg_pcl_precision_rate]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["Source", "Average Precision Rate"]),
                    cells=dict(values=[source_precision_rate, values_precision_rate]),
                )
            ]
        )
        plot_titles.append("Average Precision Rate rate for parking markers")
        plots.append(fig)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[timeframe.timestamp for timeframe in pcl_data],
                y=[len(timeframe.pcl_delimiter_array) for timeframe in pcl_data],
                mode="lines",
                name="Number of CEM PCL",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[timestamp for timestamp, _ in number_associated_pcl],
                y=[nbr_associated for _, nbr_associated in number_associated_pcl],
                mode="lines",
                name="Number of associated CEM PCL to the ground truth (TP)",
            )
        )
        plot_titles.append("Total number of CEM PCL vs. associated (TP)")
        plots.append(fig)
        remarks.append("")

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM PFS PCL Precision Rate",
    description="This KPI provides the average precision rate of the PCL lines in the CEM output,\
         Precision = TP / ( TP + FP)",
)
class KpiPCLPrecisionRate(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepKpiPCLPrecisionRate]


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL Output",
    description="This test case checks if PFS performs the fusion based on incoming parking marker detections"
    "and provide a list of tracked Parking Markers.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLOutput(TestStep):
    """TestStep for evaluating output in PCL, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        pcl_data = PclDelimiterReader(reader).convert_to_class()
        data_df = reader.as_plain_df
        pmd_data = data_df[
            [
                "PMDCamera_Front_numberOfLines",
                "PMDCamera_Front_timestamp",
                "PMDCamera_Rear_numberOfLines",
                "PMDCamera_Rear_timestamp",
                "PMDCamera_Left_numberOfLines",
                "PMDCamera_Left_timestamp",
                "PMDCamera_Right_numberOfLines",
                "PMDCamera_Right_timestamp",
            ]
        ]

        # Check if there are PM in the data
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

        # Get the first TS where there is an input in all cameras
        first_in_ts = min(
            [
                pmd_data[pmd_data["PMDCamera_Front_numberOfLines"] > 0]["PMDCamera_Front_timestamp"].min(),
                pmd_data[pmd_data["PMDCamera_Rear_numberOfLines"] > 0]["PMDCamera_Rear_timestamp"].min(),
                pmd_data[pmd_data["PMDCamera_Left_numberOfLines"] > 0]["PMDCamera_Left_timestamp"].min(),
                pmd_data[pmd_data["PMDCamera_Right_numberOfLines"] > 0]["PMDCamera_Right_timestamp"].min(),
            ]
        )

        # Get the last TS where there is an output in all cameras
        last_in_ts = max(
            [
                pmd_data[pmd_data["PMDCamera_Front_numberOfLines"] > 0]["PMDCamera_Front_timestamp"].max(),
                pmd_data[pmd_data["PMDCamera_Rear_numberOfLines"] > 0]["PMDCamera_Rear_timestamp"].max(),
                pmd_data[pmd_data["PMDCamera_Left_numberOfLines"] > 0]["PMDCamera_Left_timestamp"].max(),
                pmd_data[pmd_data["PMDCamera_Right_numberOfLines"] > 0]["PMDCamera_Right_timestamp"].max(),
            ]
        )

        # Calculate delay
        delay = ConstantsCem.SYNC_INPUT_OUTPUT_CYCLES * ConstantsCem.CYCLE_PERIOD_TIME_MS
        first_out_ts = first_in_ts + (delay * 1e3)
        last_out_ts = last_in_ts + (delay * 1e3)

        if ConstantsCemInput.PCLEnum in pcl_type.values:
            rows = []
            failed_timestamps = 0
            for _, cur_timeframe in enumerate(pcl_data):
                pcl_number = len(cur_timeframe.pcl_delimiter_array)
                cur_timestamp = cur_timeframe.timestamp
                if cur_timestamp <= first_in_ts:
                    if pcl_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["First zone, no input marker"], ["No output"]]
                        rows.append(values)

                elif first_in_ts <= cur_timestamp < first_out_ts:
                    if pcl_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["Second zone, input markers"], ["No output"]]
                        rows.append(values)

                elif first_out_ts <= cur_timestamp < last_in_ts:
                    if pcl_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["Third zone, input markers"], ["Output available"]]
                        rows.append(values)

                elif last_in_ts <= cur_timestamp < last_out_ts:
                    if pcl_number == 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["Fourth zone, no input marker"], ["Output available"]]
                        rows.append(values)

                else:
                    if pcl_number != 0:
                        failed_timestamps += 1
                        values = [[cur_timestamp], [pcl_number], ["Fifth zone, no input markers"], ["No output"]]
                        rows.append(values)

            if failed_timestamps:
                test_result = fc.FAIL
            else:
                test_result = fc.PASS

            # Plots
            header = ["Timestamp", "Number of output markers", "Evaluation section", "Expected result"]
            values = list(zip(*rows))
            fig = go.Figure(data=[go.Table(header=dict(values=header), cells=dict(values=values))])
            plot_titles.append("Test Fail report")
            plots.append(fig)
            remarks.append("")

            pmd_front = pmd_data[["PMDCamera_Front_numberOfLines", "PMDCamera_Front_timestamp"]].drop_duplicates()
            pmd_front = pmd_front.loc[(pmd_front["PMDCamera_Front_timestamp"] != 0)]
            pmd_rear = pmd_data[["PMDCamera_Rear_numberOfLines", "PMDCamera_Rear_timestamp"]].drop_duplicates()
            pmd_rear = pmd_rear.loc[(pmd_rear["PMDCamera_Rear_timestamp"] != 0)]
            pmd_left = pmd_data[["PMDCamera_Left_numberOfLines", "PMDCamera_Left_timestamp"]].drop_duplicates()
            pmd_left = pmd_left.loc[(pmd_left["PMDCamera_Left_timestamp"] != 0)]
            pmd_right = pmd_data[["PMDCamera_Right_numberOfLines", "PMDCamera_Right_timestamp"]].drop_duplicates()
            pmd_right = pmd_right.loc[(pmd_right["PMDCamera_Right_timestamp"] != 0)]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=data_df["numPclDelimiters_timestamp"], y=data_df["numPclDelimiters"], name="Output")
            )
            fig.add_vrect(
                x0=data_df["numPclDelimiters_timestamp"].iat[0], x1=first_in_ts, fillcolor="#F3E5F5", layer="below"
            )
            fig.add_vrect(x0=first_in_ts, x1=first_out_ts, layer="below")
            fig.add_vrect(x0=first_out_ts, x1=last_in_ts, fillcolor="#F5F5F5", layer="below")
            fig.add_vrect(x0=last_in_ts, x1=last_out_ts, layer="below")
            fig.add_vrect(
                x0=last_out_ts, x1=data_df["numPclDelimiters_timestamp"].iat[-1], fillcolor="#F3E5F5", layer="below"
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_front["PMDCamera_Front_timestamp"],
                    y=pmd_front["PMDCamera_Front_numberOfLines"],
                    name="pmd_front",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_rear["PMDCamera_Rear_timestamp"], y=pmd_rear["PMDCamera_Rear_numberOfLines"], name="pmd_rear"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_left["PMDCamera_Left_timestamp"], y=pmd_left["PMDCamera_Left_numberOfLines"], name="pmd_left"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=pmd_right["PMDCamera_Right_timestamp"],
                    y=pmd_right["PMDCamera_Right_numberOfLines"],
                    name="pmd_right",
                )
            )
            plots.append(fig)
            plot_titles.append("Evaluated zones")
            remarks.append("")

        else:
            test_result = fc.INPUT_MISSING

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM PFS PCL Output",
    description="This test case checks if PFS performs the fusion based on incoming parking marker detections"
    "and provide a list of tracked Parking Markers.",
)
class FtPCLOutput(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLOutput]


@teststep_definition(
    step_number=1,
    name="CEM-PFS Al Signal State",
    description="This test case checks if PFS only processes input signals if their signal state is AL_SIG_STATE_OK",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLAlSignalState(TestStep):
    """TestStep for assessing AL signal states in PCL, utilizing a custom report."""

    custom_report = CustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        df = reader.as_plain_df

        # Output df
        pcl_data = df[["numPclDelimiters_timestamp", "Pcl_eSigStatus", "numPclDelimiters"]]
        slot_data = df[["CemSlot_timestamp", "CemSlot_eSigStatus", "CemSlot_numberOfSlots"]]
        # TODO: Empty cycles at the beginning of data ts=0 check if reset signal resets timestamps to apply filter
        # Input df
        pmd_data = df[
            [
                "PMDCamera_Front_timestamp",
                "PMDCamera_Front_eSigStatus",
                "PMDCamera_Front_numberOfLines",
                "PMDCamera_Rear_timestamp",
                "PMDCamera_Rear_eSigStatus",
                "PMDCamera_Rear_numberOfLines",
                "PMDCamera_Left_timestamp",
                "PMDCamera_Left_eSigStatus",
                "PMDCamera_Left_numberOfLines",
                "PMDCamera_Right_timestamp",
                "PMDCamera_Right_eSigStatus",
                "PMDCamera_Right_numberOfLines",
            ]
        ]
        wsd_data = df[
            [
                "CemWs_Front_timestamp",
                "CemWs_Front_eSigStatus",
                "CemWs_Front_numberOfLines",
                "CemWs_Rear_timestamp",
                "CemWs_Rear_eSigStatus",
                "CemWs_Rear_numberOfLines",
                "CemWs_Left_timestamp",
                "CemWs_Left_eSigStatus",
                "CemWs_Left_numberOfLines",
                "CemWs_Right_timestamp",
                "CemWs_Right_eSigStatus",
                "CemWs_Right_numberOfLines",
            ]
        ]
        # TODO: Signal status for all bsigs not available update common_ft_helper
        psd_data = df[
            [
                "PsdSlot_Front_timestamp",
                "PsdSlot_Front_eSigStatus",
                "PsdSlot_Front_numberOfSlots",
                "PsdSlot_Rear_timestamp",
                "PsdSlot_Rear_eSigStatus",
                "PsdSlot_Rear_numberOfSlots",
                "PsdSlot_Left_timestamp",
                "PsdSlot_Left_eSigStatus",
                "PsdSlot_Left_numberOfSlots",
                "PsdSlot_Right_timestamp",
                "PsdSlot_Rigth_eSigStatus",
                "PsdSlot_Right_numberOfSlots",
            ]
        ]

        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
        pcl_type = df.loc[:, df.columns.str.startswith("delimiterType")]

        # TODO: Refactor pending
        if ConstantsCemInput.PCLEnum in pcl_type.values:
            # PDM signals ranges
            pmd_ok_ts = [
                pmd_data[PMDCamera.FRONT].query("signalState == 1")["timestamp"].min(),
                pmd_data[PMDCamera.REAR].query("signalState == 1")["timestamp"].min(),
                pmd_data[PMDCamera.LEFT].query("signalState == 1")["timestamp"].min(),
                pmd_data[PMDCamera.RIGHT].query("signalState == 1")["timestamp"].min(),
            ]

            first_pmd_ts = min(pmd_ok_ts)
            all_pmd_ts = max(pmd_ok_ts)

            # WSD signal ranges
            wsd_ok_ts = [
                wsd_data[PMDCamera.FRONT].query("signalState == 1")["timestamp"].min(),
                wsd_data[PMDCamera.REAR].query("signalState == 1")["timestamp"].min(),
                wsd_data[PMDCamera.LEFT].query("signalState == 1")["timestamp"].min(),
                wsd_data[PMDCamera.RIGHT].query("signalState == 1")["timestamp"].min(),
            ]

            first_wsd_ts = min(wsd_ok_ts)
            all_wsd_ts = max(wsd_ok_ts)

            # PSD signal ranges
            psd_ok_ts = [
                psd_data[psd_data["Front_signalState"] == 1]["Front_timestamp"].min(),
                psd_data[psd_data["Rear_signalState"] == 1]["Rear_timestamp"].min(),
                psd_data[psd_data["Left_signalState"] == 1]["Left_timestamp"].min(),
                psd_data[psd_data["Right_signalState"] == 1]["Right_timestamp"].min(),
            ]

            first_psd_ts = min(psd_ok_ts)
            all_psd_ts = max(psd_ok_ts)

            # Get ok status ts PCL data
            first_in_ts = min(first_pmd_ts, first_wsd_ts)
            all_in_ts = max(all_wsd_ts, all_pmd_ts)

            # Find closest ts where input signal state changes from 0 to 1 PCL data
            pcl_first_closest_ts = pcl_data.loc[pcl_data["timestamp"] > first_in_ts, "timestamp"].min()
            # Find closest ts where all inputs change from 0 to 1 PCL data
            pcl_all_closest_ts = pcl_data.loc[pcl_data["timestamp"] > all_in_ts, "timestamp"].min()

            # Find closest ts where input signal state changes from 0 to 1 PS data
            psd_first_closest_ts = slot_data.loc[slot_data["timestamp"] > first_psd_ts, "timestamp"].min()
            # Find closest ts where all inputs change from 0 to 1 PS data
            psd_all_closest_ts = slot_data.loc[slot_data["timestamp"] > all_psd_ts, "timestamp"].min()

            # Find ts where there must be data in the output
            processing_tolerance = ConstantsCem.CYCLE_PERIOD_TIME_MS * ConstantsCem.NUM_OF_CYCLES_FOR_OUTPUT * 1e3
            processing_end_ts = pcl_data.loc[
                pcl_data.timestamp > pcl_first_closest_ts + processing_tolerance, "timestamp"
            ].min()

            failing_section = []
            expected_result = []
            result_provided = []
            section_range = []

            # Confirm there is no output in the first section
            pcl_section_1st = pcl_data.loc[
                pcl_data["timestamp"] < pcl_first_closest_ts, ["timestamp", "numPclDelimiters"]
            ]
            psd_section_1st = slot_data.loc[
                slot_data["timestamp"] < psd_first_closest_ts, ["timestamp", "numberOfSlots"]
            ]
            if (pcl_section_1st["numPclDelimiters"] == 0).all() and (psd_section_1st["numberOfSlots"] == 0).all():
                first_section_result = True
            else:
                first_section_result = False
                failing_section.append("First scenario")
                expected_result.append("Number of elements = 0")
                result_provided.append(
                    [pcl_section_1st["numPclDelimiters"].max(), psd_section_1st["numberOfSlots"].max()]
                )
                section_range.append(f"0 - {pcl_first_closest_ts}")

            # Confirm there is output in the second section
            pcl_section_2nd = pcl_data.loc[pcl_data["timestamp"] > processing_end_ts, ["timestamp", "numPclDelimiters"]]
            psd_section_2nd = slot_data.loc[slot_data["timestamp"] > processing_end_ts, ["timestamp", "numberOfSlots"]]
            if (pcl_section_2nd["numPclDelimiters"] > 0).all() and (psd_section_2nd["numberOfSlots"] > 0).all():
                second_section_result = True
            else:
                first_section_result = False
                failing_section.append("Second scenario")
                expected_result.append("Number of elements > 0")
                result_provided.append(
                    [pcl_section_1st["numPclDelimiters"].min(), psd_section_1st["numberOfSlots"].min()]
                )
                section_range.append(f"{pcl_first_closest_ts} - end")

            # Test pass if all sections pass
            if first_section_result and second_section_result:
                test_result = fc.PASS
            else:
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(
                                values=[
                                    "Failing section",
                                    "Expected output",
                                    "Number of elements PCL,PS",
                                    "Output section range",
                                ]
                            ),
                            cells=dict(values=[failing_section, expected_result, result_provided, section_range]),
                        )
                    ]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")

            # Plot PM data
            pcl_data = pcl_data.loc[(pcl_data["timestamp"] != 0)].drop_duplicates()
            pmd_front = pmd_data[PMDCamera.FRONT].loc[(pmd_data[PMDCamera.FRONT]["timestamp"] != 0)].drop_duplicates()
            pmd_rear = pmd_data[PMDCamera.REAR].loc[(pmd_data[PMDCamera.REAR]["timestamp"] != 0)].drop_duplicates()
            pmd_left = pmd_data[PMDCamera.LEFT].loc[(pmd_data[PMDCamera.LEFT]["timestamp"] != 0)].drop_duplicates()
            pmd_right = pmd_data[PMDCamera.RIGHT].loc[(pmd_data[PMDCamera.RIGHT]["timestamp"] != 0)].drop_duplicates()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=pcl_data["timestamp"], y=pcl_data["numPclDelimiters"], name="Output"))
            fig.add_vrect(x0=pcl_data["timestamp"].iat[0], x1=pcl_first_closest_ts, layer="below")
            fig.add_vrect(x0=processing_end_ts, x1=pcl_all_closest_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(x0=pcl_all_closest_ts, x1=pcl_data["timestamp"].iat[-1], fillcolor="#BBDEFB", layer="below")
            fig.add_trace(go.Scatter(x=pmd_front["timestamp"], y=pmd_front["signalState"], name="pmd_front"))
            fig.add_trace(go.Scatter(x=pmd_rear["timestamp"], y=pmd_rear["signalState"], name="pmd_rear"))
            fig.add_trace(go.Scatter(x=pmd_left["timestamp"], y=pmd_left["signalState"], name="pmd_left"))
            fig.add_trace(go.Scatter(x=pmd_right["timestamp"], y=pmd_right["signalState"], name="pmd_right"))
            plots.append(fig)
            plot_titles.append("Signal state PMD data")
            remarks.append("")

            # Plot WS data
            wsd_front = wsd_data[PMDCamera.FRONT].loc[(wsd_data[PMDCamera.FRONT]["timestamp"] != 0)].drop_duplicates()
            wsd_rear = wsd_data[PMDCamera.REAR].loc[(wsd_data[PMDCamera.REAR]["timestamp"] != 0)].drop_duplicates()
            wsd_left = wsd_data[PMDCamera.LEFT].loc[(wsd_data[PMDCamera.LEFT]["timestamp"] != 0)].drop_duplicates()
            wsd_right = wsd_data[PMDCamera.RIGHT].loc[(wsd_data[PMDCamera.RIGHT]["timestamp"] != 0)].drop_duplicates()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=pcl_data["timestamp"], y=pcl_data["numPclDelimiters"], name="Output"))
            fig.add_vrect(x0=pcl_data["timestamp"].iat[0], x1=pcl_first_closest_ts, layer="below")
            fig.add_vrect(x0=processing_end_ts, x1=pcl_all_closest_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(x0=pcl_all_closest_ts, x1=pcl_data["timestamp"].iat[-1], fillcolor="#BBDEFB", layer="below")
            fig.add_trace(go.Scatter(x=wsd_front["timestamp"], y=wsd_front["signalState"], name="wsd_front"))
            fig.add_trace(go.Scatter(x=wsd_rear["timestamp"], y=wsd_rear["signalState"], name="wsd_rear"))
            fig.add_trace(go.Scatter(x=wsd_left["timestamp"], y=wsd_left["signalState"], name="wsd_left"))
            fig.add_trace(go.Scatter(x=wsd_right["timestamp"], y=wsd_right["signalState"], name="wsd_right"))
            plots.append(fig)
            plot_titles.append("Signal state WSD data")
            remarks.append("")

            # Plot PS data
            psd_data = psd_data.drop_duplicates()
            psd_data = psd_data.loc[(psd_data["Front_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["Rear_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["Left_timestamp"] != 0)]
            psd_data = psd_data.loc[(psd_data["Right_timestamp"] != 0)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=slot_data["timestamp"], y=slot_data["numberOfSlots"], name="Output"))
            fig.add_vrect(x0=slot_data["timestamp"].iat[0], x1=psd_first_closest_ts, layer="below")
            fig.add_vrect(x0=processing_end_ts, x1=psd_all_closest_ts, fillcolor="#E1F5FE", layer="below")
            fig.add_vrect(x0=psd_all_closest_ts, x1=pcl_data["timestamp"].iat[-1], fillcolor="#F5F5F5", layer="below")
            fig.add_trace(go.Scatter(x=psd_data["Front_timestamp"], y=psd_data["Front_signalState"], name="psdFront"))
            fig.add_trace(go.Scatter(x=psd_data["Rear_timestamp"], y=psd_data["Rear_signalState"], name="psdRear"))
            fig.add_trace(go.Scatter(x=psd_data["Left_timestamp"], y=psd_data["Left_signalState"], name="psdLeft"))
            fig.add_trace(go.Scatter(x=psd_data["Right_timestamp"], y=psd_data["Right_signalState"], name="psdRight"))
            plots.append(fig)
            plot_titles.append("Signal state PSD data")
            remarks.append("")

        else:
            test_result = fc.INPUT_MISSING

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="CEM-PFS Al Signal State",
    description="This test case checks if PFS only processes input signals if their signal state is AL_SIG_STATE_OK",
)
class FtPCLAlSignalState(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLAlSignalState]
