"""CEM TPF Test Cases"""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import math
import typing

import numpy as np
import pandas as pd
import plotly.graph_objects as go

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import CemSignals, CustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import ConstantsCem, GroundTruthTpf
from pl_parking.PLP.CEM.ft_tpf_helper import FtTPFHelper, TpfFtp2GtAssociator, TPFMetricsHelper
from pl_parking.PLP.CEM.inputs.input_CemTpfReader import DynamicObject, MaintenanceState, TPFReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader
from pl_parking.PLP.CEM.inputs.input_DynamicObjectDetection import (
    DynamicObjectCamera,
    DynamicObjectDetection,
    DynamicObjectDetectionReader,
)

SIGNAL_DATA = "CEM-TPF_FTP_confidence_decrease_check"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM-TPF FTP confidence decrease check",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtFTPConfidenceDecreaseCheck(TestStep):
    """TestStep for FTP Confidence Decrease Check, utilizing a custom report."""

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
        tpf_reader = TPFReader(reader)
        tpf_data = tpf_reader.convert_to_class()

        tpf_object_previous_state: typing.Dict[int, (int, int, MaintenanceState)] = {}

        if tpf_reader.number_of_objects > 0:
            failed = 0
            for timeframe in tpf_data:
                for tpf_object in timeframe.dynamic_objects:
                    if tpf_object.object_id in tpf_object_previous_state:
                        prev_timestamp, prev_existence_prob, prev_state = tpf_object_previous_state[
                            tpf_object.object_id
                        ]

                        timestamp_diff = (timeframe.timestamp - prev_timestamp) * 1e-6

                        if (
                            timestamp_diff < ConstantsCem.AP_E_DYN_OBJ_ID_REUSE_TIME_S
                            and prev_state != MaintenanceState.DELETED
                        ):

                            if tpf_object.state == MaintenanceState.PREDICTED and FtTPFHelper.is_object_in_car_FOV(
                                tpf_object
                            ):
                                if tpf_object.existence_prob >= prev_existence_prob:
                                    failed += 1

                    if tpf_object.state == MaintenanceState.DELETED:
                        if tpf_object.object_id in tpf_object_previous_state:
                            tpf_object_previous_state.pop(tpf_object.object_id)
                    else:
                        tpf_object_previous_state[tpf_object.object_id] = (
                            timeframe.timestamp,
                            tpf_object.existence_prob,
                            tpf_object.state,
                        )

            if failed:
                test_result = fc.FAIL
                test_fail_message = (
                    "FTP is in car FoV and not measured but the " + "probability of existence is not decreased."
                )
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Failing message", "Number of failed objects"]),
                            cells=dict(values=[[test_fail_message], [failed]]),
                        )
                    ]
                )
                plot_titles.append("")
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
    name="CEM-TPF FTP confidence decrease check",
    description="---NOT USED---- "
    "The test checks that CEM decrease the probability of existence in case the object in FoV camera"
    "and is not reported as an RTP.",
)
class FtFTPConfidenceDecreaseCheck(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtFTPConfidenceDecreaseCheck]


@teststep_definition(
    step_number=1,
    name="CEM-TPF FTP Confidence check when object is measured",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtFTPConfidenceObjectMeasured(TestStep):
    """TestStep for FTP Confidence Object Measured, utilizing a custom report."""

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
        tpf_reader = TPFReader(reader)
        tpf_data = tpf_reader.convert_to_class()
        input_reader = DynamicObjectDetectionReader(reader)
        rtp_data = input_reader.convert_to_class()

        # TODO: do we really need this?
        # if not FtTPFHelper.check_only_one_camera_is_active(rtp_data):
        #     test_result = fc.INPUT_MISSING
        #     test_fail_message = "Recording should contain dynamic object(s) receieved only from single camera"

        if tpf_reader.number_of_objects > 0:
            # object_id: (timestamp, existence_prob, state)
            tpf_object_previous_state: typing.Dict[int, (int, int, MaintenanceState)] = {}

            failed = 0
            for tpf_timeframe in tpf_data:
                cnt_tpf_objects = len(tpf_timeframe.dynamic_objects)
                association_with_min_prob: typing.List[DynamicObjectDetection] = [None] * cnt_tpf_objects

                for _, rtp_timeframe_list in rtp_data.items():
                    relevent_rtp_timeframe = FtTPFHelper.get_single_relevant_RTP_frame(
                        rtp_timeframe_list, tpf_timeframe.timestamp
                    )
                    if relevent_rtp_timeframe is not None:
                        association_per_camera: typing.List[typing.List[DynamicObjectDetection]] = (
                            FtTPFHelper.associate_RTP_To_FTP(
                                tpf_timeframe.dynamic_objects, relevent_rtp_timeframe.dynamic_objects
                            )
                        )

                    for i in range(cnt_tpf_objects):
                        for associated_rtp in association_per_camera[i]:
                            if (
                                association_with_min_prob[i] is None
                                or association_with_min_prob[i].confidence > associated_rtp.confidence
                            ):
                                association_with_min_prob[i] = associated_rtp

                for i, tpf_object in enumerate(tpf_timeframe.dynamic_objects):
                    if tpf_object.object_id in tpf_object_previous_state:
                        prev_timestamp, prev_existence_prob, prev_state = tpf_object_previous_state[
                            tpf_object.object_id
                        ]

                        timestamp_diff = (tpf_timeframe.timestamp - prev_timestamp) * 1e-6

                        if (
                            timestamp_diff < ConstantsCem.AP_E_DYN_OBJ_ID_REUSE_TIME_S
                            and prev_state != MaintenanceState.DELETED
                        ):

                            if (
                                tpf_object.state == MaintenanceState.MEASURED
                                and association_with_min_prob[i] is not None
                                and association_with_min_prob[i].confidence >= prev_existence_prob
                            ):
                                if tpf_object.existence_prob < prev_existence_prob:
                                    failed += 1

                    if tpf_object.state == MaintenanceState.DELETED:
                        if tpf_object.object_id in tpf_object_previous_state:
                            tpf_object_previous_state.pop(tpf_object.object_id)
                    else:
                        tpf_object_previous_state[tpf_object.object_id] = (
                            tpf_timeframe.timestamp,
                            tpf_object.existence_prob,
                            tpf_object.state,
                        )

            if failed:
                test_result = fc.FAIL
                test_fail_message = (
                    "SVC provides object with higher confidence but CEM gives " + "it with lower confidence"
                )
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Failing message", "Number of failed objects"]),
                            cells=dict(values=[[test_fail_message], [failed]]),
                        )
                    ]
                )
                plot_titles.append("Number of failed objects")
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


@verifies("38917", doors_url="")
@testcase_definition(
    doors_url="1521998",
    name="CEM-TPF FTP Confidence check when object is measured",
    description="The test is to check that when an object is confirmed by the same sensor with equal or greater prob,"
    " its probability of existence is not decreased.",
)
class FtFTPConfidenceObjectMeasured(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtFTPConfidenceObjectMeasured]


@teststep_definition(
    step_number=1,
    name="CEM-TPF FTP Confidence check when object is not measured",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtFTPConfidenceObjectNotMeasured(TestStep):
    """TestStep for FTP Confidence Object Not Measured, utilizing a custom report."""

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
        tpf_reader = TPFReader(reader)
        tpf_data = tpf_reader.convert_to_class()

        # object_id: (timestamp, existence_prob, state)
        tpf_object_previous_state: typing.Dict[int, (int, int, MaintenanceState)] = {}

        if tpf_reader.number_of_objects > 0:
            rows = []
            failed = 0
            for timeframe in tpf_data:
                for tpf_object in timeframe.dynamic_objects:
                    if tpf_object.object_id in tpf_object_previous_state:
                        prev_timestamp, prev_existence_prob, prev_state = tpf_object_previous_state[
                            tpf_object.object_id
                        ]

                        timestamp_diff = (timeframe.timestamp - prev_timestamp) * 1e-6

                        if (
                            timestamp_diff < ConstantsCem.AP_E_DYN_OBJ_ID_REUSE_TIME_S
                            and prev_state != MaintenanceState.DELETED
                        ):

                            if (
                                tpf_object.state == MaintenanceState.PREDICTED
                                and prev_state == MaintenanceState.PREDICTED
                                and tpf_object.existence_prob > prev_existence_prob
                            ):
                                failed += 1
                                values = [
                                    [timeframe.timestamp],
                                    [tpf_object.existence_prob],
                                    [prev_existence_prob],
                                    [tpf_object.object_id],
                                ]
                                rows.append(values)

                    if tpf_object.state == MaintenanceState.DELETED:
                        if tpf_object.object_id in tpf_object_previous_state:
                            tpf_object_previous_state.pop(tpf_object.object_id)
                    else:
                        tpf_object_previous_state[tpf_object.object_id] = (
                            timeframe.timestamp,
                            tpf_object.existence_prob,
                            tpf_object.state,
                        )

            if failed:
                test_result = fc.FAIL
                test_fail_message = "Confidence value is increasing while FTP is not measured."
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Failing message", "Number of failed objects"]),
                            cells=dict(values=[[test_fail_message], [failed]]),
                        )
                    ]
                )
                plot_titles.append("Number of failed objects")
                plots.append(fig)
                remarks.append("")

                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(
                                values=["Timestamp", "Current probability", "Previous probability", "Object ID"]
                            ),
                            cells=dict(values=values),
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
    name="CEM-TPF FTP Confidence check when object is not measured",
    description="The test is to check that when an object is not observed by any sensor,"
    "its probability of existence is not increased.",
)
class FtFTPConfidenceObjectNotMeasured(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtFTPConfidenceObjectNotMeasured]


@teststep_definition(
    step_number=1,
    name="CEM-TPF FTP ID Maintenance Check ",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtFTPIDMaintenance(TestStep):
    """TestStep for FTP ID Maintenance, utilizing a custom report."""

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
        inputReader = TPFReader(reader)
        tpfData = inputReader.convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()

        if inputReader.number_of_objects > 0:
            rows = []
            failed = 0
            for index, cur_time_frame in enumerate(tpfData):
                if index > 0:
                    prev_time_frame = tpfData[index - 1]
                    for cur_object in cur_time_frame.dynamic_objects:
                        if cur_object.state == MaintenanceState.MEASURED:
                            time_stamp_diff = cur_time_frame.timestamp - prev_time_frame.timestamp
                            # Store possible associations to avoid test fail in case of multiple possible associations
                            associated_prev_object: typing.List[DynamicObject] = []

                            relative_motion = vedodo_buffer.calc_relative_motion(
                                cur_time_frame.timestamp, prev_time_frame.timestamp
                            )

                            for prev_object in prev_time_frame.dynamic_objects:
                                if FtTPFHelper.is_current_associated_to_prev(
                                    cur_object, prev_object, time_stamp_diff, relative_motion
                                ):
                                    associated_prev_object.append(prev_object)
                            if len(associated_prev_object) == 1:
                                if associated_prev_object[0].object_id != cur_object.object_id:
                                    failed += 1
                                    values = [[cur_time_frame.timestamp], [cur_object.object_id]]
                                    rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(data=[go.Table(header=dict(values=["Timestamp", "FTP_ID"]), cells=dict(values=values))])
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
    name="CEM-TPF FTP ID Maintenance Check ",
    description="If a RTP is received in the current cycle and is associated to a FTP which EnvironmentFusion"
    "provided in the previous cycle with an unique ID, CEM-SW shall provide the same ID of this"
    "updated FTP in the current cycle.",
)
class FtFTPIDMaintenance(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtFTPIDMaintenance]


@teststep_definition(
    step_number=1,
    name="CEM-TPF FTP ID Reuse",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtFTPIDReuse(TestStep):
    """TestStep for FTP ID Reuse, utilizing a custom report."""

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
        inputReader = TPFReader(reader)
        tpfData = inputReader.convert_to_class()

        timestamp_for_ids_stop: typing.Dict[int, int] = {}

        if inputReader.number_of_objects > 0:
            rows = []
            failed = 0
            for index, time_frame in enumerate(tpfData):
                if index == len(tpfData) - 1:
                    continue
                for object in time_frame.dynamic_objects:
                    if object.object_id in timestamp_for_ids_stop:
                        time_diff = (time_frame.timestamp - timestamp_for_ids_stop[object.object_id]) * 1e-6
                        if time_diff < ConstantsCem.AP_E_DYN_OBJ_ID_REUSE_TIME_S:
                            failed += 1
                            values = [[object.timestamp], [time_diff]]
                            rows.append(values)
                        else:
                            timestamp_for_ids_stop.pop(object.object_id)
                    if not FtTPFHelper.check_if_object_in_timeframe(object, tpfData[index + 1]):
                        timestamp_for_ids_stop[object.object_id] = time_frame.timestamp

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[go.Table(header=dict(values=["Timestamp", "Time Difference"]), cells=dict(values=values))]
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
    name="CEM-TPF FTP ID Reuse",
    description=f"""This test checks that when an object ID of an FTP is stopped being provided
                it wont be assigned immediately for a new one until {ConstantsCem.AP_E_DYN_OBJ_ID_REUSE_TIME_S} s""",
)
class FtFTPIDReuse(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtFTPIDReuse]


@teststep_definition(
    step_number=1,
    name="CEM-TPF FTP Prediction Time Check ",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtFTPMeasured(TestStep):
    """TestStep for FTP Measured, utilizing a custom report."""

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
        inputReader = TPFReader(reader)
        tpfData = inputReader.convert_to_class()

        prediction_start_timestamp: typing.Dict[int, int] = {}

        if inputReader.number_of_objects > 0:
            failed = 0
            rows = []
            for index, time_frame in enumerate(tpfData):
                if index == len(tpfData) - 1:
                    continue
                for object in time_frame.dynamic_objects:
                    if not FtTPFHelper.check_if_object_in_timeframe(object, tpfData[index + 1]):
                        diff = 0
                        if object.object_id in prediction_start_timestamp:
                            diff = abs(prediction_start_timestamp[object.object_id] - time_frame.timestamp) * 1e-6
                        if (
                            diff < ConstantsCem.AP_E_DYN_OBJ_MIN_TRACKING_TIME_S
                            or diff > ConstantsCem.AP_E_DYN_OBJ_MAX_TRACKING_TIME_S
                        ):
                            failed += 1
                            values = [
                                [time_frame.timestamp],
                                [object.object_id],
                                [prediction_start_timestamp[object.object_id]],
                                [diff],
                            ]
                            rows.append(values)

                    if object.object_id in prediction_start_timestamp:
                        if object.state == MaintenanceState.MEASURED:
                            prediction_start_timestamp.pop(object.object_id)

                    elif object.state == MaintenanceState.PREDICTED:
                        prediction_start_timestamp[object.object_id] = time_frame.timestamp

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Timestamp", "FTP_ID", "Prediction Started", "Prediction time [s]"]),
                            cells=dict(values=values),
                        )
                    ]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = (fc.PASS,)

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
    name="CEM-TPF FTP Prediction Time Check ",
    description="Validate the maximum prediction time of a valid FTP when none of the sensors are detecting.",
)
class FtFTPMeasured(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtFTPMeasured]


@teststep_definition(
    step_number=1,
    name="CEM-TPF FTP Reference Point check ",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtFTPReferencePointCheck(TestStep):
    """TestStep for FTP Reference Point Check, utilizing a custom report."""

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
        input_reader = TPFReader(reader)
        tpf_data = input_reader.convert_to_class()
        test_fail_message = "Data not available"

        def calc_dist(x1, y1, x2, y2):
            dx = x1 - x2
            dy = y1 - y2
            return math.sqrt(dx * dx + dy * dy)

        if input_reader.number_of_objects > 0:
            failed = 0
            for timeframe in tpf_data:
                for tpf_object in timeframe.dynamic_objects:
                    distances = [
                        calc_dist(
                            tpf_object.center_x, tpf_object.center_y, tpf_object.shape[i].x, tpf_object.shape[i].y
                        )
                        for i in range(4)
                    ]

                    diff = np.max(distances) - np.min(distances)

                    if diff > 1e-2:
                        failed += 1

            if failed:
                test_result = fc.FAIL
                test_fail_message = f"The reference point is not in the center of the object (difference = {diff} m)"
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Failing message", "Number of failed objects"]),
                            cells=dict(values=[[test_fail_message], [failed]]),
                        )
                    ]
                )
                plot_titles.append("")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

        else:
            test_result = fc.INPUT_MISSING

        if test_result != fc.PASS:
            fig = go.Figure(
                data=[go.Table(header=dict(values=["Failing message"]), cells=dict(values=[[test_fail_message]]))]
            )
            plot_titles.append("")
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
    name="CEM-TPF FTP Reference Point check ",
    description="EnvironmentFusion shall provide the TP's reference point in the center of the provided TP object.",
)
class FtFTPReferencePointCheck(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtFTPReferencePointCheck]


@teststep_definition(
    step_number=1,
    name="CEM-TPF FTP Unique ID",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtFTPUniqueID(TestStep):
    """TestStep for FTP Unique ID, utilizing a custom report."""

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
        inputReader = TPFReader(reader)
        tpfData = inputReader.convert_to_class()

        if inputReader.number_of_objects > 0:
            rows = []
            failed = 0
            for time_frame in tpfData:
                ids = []
                for object in time_frame.dynamic_objects:
                    if object.object_id in ids:
                        failed += 1
                        values = [[object.timestamp], [object.object_id]]
                        rows.append(values)
                    else:
                        ids.append(object.object_id)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(data=[go.Table(header=dict(values=["Timestamp", "FTP_ID"]), cells=dict(values=values))])
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
    name="CEM-TPF FTP Unique ID",
    description="This test test if EnvironmentFusion provides a unique ID for all FTP in all timeframe.",
)
class FtFTPUniqueID(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtFTPUniqueID]


@teststep_definition(
    step_number=1,
    name="CEM-TPF check closest FTP are provided",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFClosestTPProvided(TestStep):
    """TestStep for TPFClosestTP Provided, utilizing a custom report."""

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
        tpf_reader = TPFReader(reader)
        tpf_data = tpf_reader.convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()

        if tpf_reader.number_of_objects > 0:
            rows = []
            failed = 0
            for i in range(len(tpf_data) - 1):
                prev_timeframe = tpf_data[i]
                cur_timeframe = tpf_data[i + 1]

                if cur_timeframe.num_objects == ConstantsCem.AP_E_DYN_OBJ_MAX_NUM_NU:
                    relative_motion = vedodo_buffer.calc_relative_motion(
                        cur_timeframe.timestamp, prev_timeframe.timestamp
                    )
                    missing_tpfs = FtTPFHelper.get_missing_tpf_objects(
                        prev_timeframe.dynamic_objects, cur_timeframe.dynamic_objects
                    )
                    transformed_missing_tpfs = [FtTPFHelper.transform_tpf(tpf, relative_motion) for tpf in missing_tpfs]

                    if len(missing_tpfs) > 0:
                        _, closest_missing_tpf_dist = FtTPFHelper.get_closest_tpf(transformed_missing_tpfs)
                        _, current_furthest_tpf_dist = FtTPFHelper.get_furthest_tpf(cur_timeframe.dynamic_objects)

                        if closest_missing_tpf_dist > current_furthest_tpf_dist:
                            failed += 1
                            values = [
                                [cur_timeframe.timestamp],
                                [closest_missing_tpf_dist],
                                [current_furthest_tpf_dist],
                            ]
                            rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Timestamp", "Closest Missing Distance", "Current furthest Distance"]),
                            cells=dict(values=values),
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
    name="CEM-TPF check closest FTP are provided",
    description=f"""The test is to check SW provides the FTPs which are closer to origin of vehicle coordinate system
                when the number of TPs exceeds {ConstantsCem.AP_E_DYN_OBJ_MAX_NUM_NU}""",
)
class FtTPFClosestTPProvided(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFClosestTPProvided]


@teststep_definition(
    step_number=1,
    name="CEM-TPF Lateral Position Accuracy",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFLateralPosAcc(TestStep):
    """TestStep for TPFLateral Position Accuracy, utilizing a custom report."""

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
        tpf_data = TPFReader(reader).convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()
        ground_truth = pd.read_hdf(os.path.dirname(__file__) + "\\" + GroundTruthTpf.tpf_gt_file[0])
        rtp_data = DynamicObjectDetectionReader(reader).convert_to_class()

        associator = TpfFtp2GtAssociator(vedodo_buffer, ground_truth)

        test_result = fc.NOT_ASSESSED

        rtp_satisfy_dynamics_acc = 0
        ftp_satisfy_dynamics_acc = 0
        ftp_satisfy_dynamics_acc_max = 0

        for tpf_timeframe in tpf_data[20:]:
            ftp_association = associator.associate(tpf_timeframe)
            gts = associator.get_gt_at_timeframe(tpf_timeframe.timestamp)
            inv_ftp_association = {v: k for k, v in ftp_association.items()}

            for camera, _ in rtp_data.items():
                rtp_timeframe = FtTPFHelper.get_single_relevant_RTP_frame(rtp_data[camera], tpf_timeframe.timestamp)
                if rtp_timeframe is None:
                    continue
                rtp_association = associator.associate(rtp_timeframe)
                for rtp_id, gt_id in rtp_association.items():
                    rtp = FtTPFHelper.get_Tp_by_id(rtp_timeframe.dynamic_objects, rtp_id)
                    gt = gts[gt_id]
                    if abs(rtp.center_y - gt["y"]) < ConstantsCem.AP_E_DYN_OBJ_ACC_Y_M(gt["y"]):
                        rtp_satisfy_dynamics_acc += 1
                        if gt_id in inv_ftp_association:
                            ftp = FtTPFHelper.get_Tp_by_id(tpf_timeframe.dynamic_objects, inv_ftp_association[gt_id])
                            ftp_acc = abs(ftp.center_y - gt["y"])
                            if ftp_acc < ConstantsCem.AP_E_DYN_OBJ_ACC_Y_M(gt["y"]):
                                ftp_satisfy_dynamics_acc += 1
                            if ftp_acc < ConstantsCem.AP_E_DYN_OBJ_ACC_MAX_Y_M(gt["y"]):
                                ftp_satisfy_dynamics_acc_max += 1

        if rtp_satisfy_dynamics_acc > 0:
            dynamics_acc_ratio = ftp_satisfy_dynamics_acc / rtp_satisfy_dynamics_acc
            dynamics_acc_ratio_max = ftp_satisfy_dynamics_acc_max / rtp_satisfy_dynamics_acc

            if (
                dynamics_acc_ratio < ConstantsCem.AP_E_DYN_OBJ_ACC_EQUAL_RATE_NU / 100.0
                or dynamics_acc_ratio_max < ConstantsCem.AP_E_DYN_OBJ_ACC_MAX_RATE_NU / 100.0
            ):
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(
                                values=[
                                    "Y accuracy ratio",
                                    "Y max accuracy ratio",
                                    "Y accuracy ratio limit",
                                    "Y max accuracy ratio limit",
                                ]
                            ),
                            cells=dict(
                                values=[
                                    [dynamics_acc_ratio * 100],
                                    [dynamics_acc_ratio_max * 100],
                                    [ConstantsCem.AP_E_DYN_OBJ_ACC_EQUAL_RATE_NU],
                                    [ConstantsCem.AP_E_DYN_OBJ_ACC_MAX_RATE_NU],
                                ]
                            ),
                        )
                    ]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

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
    name="CEM-TPF Lateral Position Accuracy",
    description="",
)
class FtTPFLateralPosAcc(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFLateralPosAcc]


@teststep_definition(
    step_number=1,
    name="CEM-TPF Longitudinal Position Accuracy",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFLongitudePosAcc(TestStep):
    """TestStep for TPFLongitude Position Accuracy, utilizing a custom report."""

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
        tpf_data = TPFReader(reader).convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()
        ground_truth = pd.read_hdf(os.path.dirname(__file__) + "\\" + GroundTruthTpf.tpf_gt_file[0])
        rtp_data = DynamicObjectDetectionReader(reader).convert_to_class()

        associator = TpfFtp2GtAssociator(vedodo_buffer, ground_truth)

        test_result = fc.NOT_ASSESSED

        rtp_satisfy_dynamics_acc = 0
        ftp_satisfy_dynamics_acc = 0
        ftp_satisfy_dynamics_acc_max = 0

        for tpf_timeframe in tpf_data[20:]:
            ftp_association = associator.associate(tpf_timeframe)
            gts = associator.get_gt_at_timeframe(tpf_timeframe.timestamp)
            inv_ftp_association = {v: k for k, v in ftp_association.items()}

            for camera, _ in rtp_data.items():
                rtp_timeframe = FtTPFHelper.get_single_relevant_RTP_frame(rtp_data[camera], tpf_timeframe.timestamp)
                if rtp_timeframe is None:
                    continue
                rtp_association = associator.associate(rtp_timeframe)
                for rtp_id, gt_id in rtp_association.items():
                    rtp = FtTPFHelper.get_Tp_by_id(rtp_timeframe.dynamic_objects, rtp_id)
                    gt = gts[gt_id]
                    if abs(rtp.center_x - gt["x"]) < ConstantsCem.AP_E_DYN_OBJ_ACC_M(gt["x"]):
                        rtp_satisfy_dynamics_acc += 1
                        if gt_id in inv_ftp_association:
                            ftp = FtTPFHelper.get_Tp_by_id(tpf_timeframe.dynamic_objects, inv_ftp_association[gt_id])
                            ftp_acc = abs(ftp.center_x - gt["x"])
                            if ftp_acc < ConstantsCem.AP_E_DYN_OBJ_ACC_M(gt["x"]):
                                ftp_satisfy_dynamics_acc += 1
                            if ftp_acc < ConstantsCem.AP_E_DYN_OBJ_ACC_MAX_M(gt["x"]):
                                ftp_satisfy_dynamics_acc_max += 1

        if rtp_satisfy_dynamics_acc > 0:
            dynamics_acc_ratio = ftp_satisfy_dynamics_acc / rtp_satisfy_dynamics_acc
            dynamics_acc_ratio_max = ftp_satisfy_dynamics_acc_max / rtp_satisfy_dynamics_acc

            if (
                dynamics_acc_ratio < ConstantsCem.AP_E_DYN_OBJ_ACC_EQUAL_RATE_NU / 100.0
                or dynamics_acc_ratio_max < ConstantsCem.AP_E_DYN_OBJ_ACC_MAX_RATE_NU / 100.0
            ):
                test_result = fc.FAIL
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(
                                values=[
                                    "X accuracy ratio",
                                    "X max accuracy ratio",
                                    "X accuracy ratio limit",
                                    "X max accuracy ratio limit",
                                ]
                            ),
                            cells=dict(
                                values=[
                                    [dynamics_acc_ratio * 100],
                                    [dynamics_acc_ratio_max * 100],
                                    [ConstantsCem.AP_E_DYN_OBJ_ACC_EQUAL_RATE_NU],
                                    [ConstantsCem.AP_E_DYN_OBJ_ACC_MAX_RATE_NU],
                                ]
                            ),
                        )
                    ]
                )
                plot_titles.append("Test Fail report")
                plots.append(fig)
                remarks.append("")
            else:
                test_result = fc.PASS

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
    name="CEM-TPF Longitudinal Position Accuracy",
    description="",
)
class FtTPFLongitudePosAcc(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFLongitudePosAcc]


@teststep_definition(
    step_number=1,
    name="CEM-TPF Predicted state check",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFPredictedStateCheck(TestStep):
    """TestStep for TPFPredicted State Check, utilizing a custom report."""

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
        tpf_reader = TPFReader(reader)
        tpf_data = tpf_reader.convert_to_class()
        rtp_data = DynamicObjectDetectionReader(reader).convert_to_class()

        if tpf_reader.number_of_objects > 0:
            rows = []
            failed = 0
            for tpf_timeframe in tpf_data:
                cnt_tpf_objects = len(tpf_timeframe.dynamic_objects)
                cnt_associated_objects = [0] * cnt_tpf_objects

                for camera, _ in rtp_data.items():
                    rtp_timeframe = FtTPFHelper.get_single_relevant_RTP_frame(rtp_data[camera], tpf_timeframe.timestamp)
                    if rtp_timeframe is not None:
                        association = FtTPFHelper.associate_RTP_To_FTP(
                            tpf_timeframe.dynamic_objects, rtp_timeframe.dynamic_objects
                        )

                        cnt_associated_objects = [
                            cnt_associated_objects[i] + len(association[i]) for i in range(cnt_tpf_objects)
                        ]

                for i, tpf_object in enumerate(tpf_timeframe.dynamic_objects):
                    if tpf_object.state == MaintenanceState.MEASURED and cnt_associated_objects[i] == 0:
                        failed += 1
                        values = [[tpf_timeframe.timestamp], [tpf_object.state]]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(data=[go.Table(header=dict(values=["Timestamp", "State"]), cells=dict(values=values))])
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
    name="CEM-TPF Predicted state check",
    description="This test checks if the object is not observed in one timeframe,"
    "its maintenance state is set to 'PREDICTED'",
)
class FtTPFPredictedStateCheck(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFPredictedStateCheck]


@teststep_definition(
    step_number=1,
    name="CEM-TPF Latency Compensation",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFOutputAtT7(TestStep):
    """TestStep for TPF Output at T7, utilizing a custom report."""

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
        # Define variables
        test_result = fc.NOT_ASSESSED
        plot_titles, plots, remarks = rep([], 3)

        # Load signals
        reader = self.readers[SIGNAL_DATA].signals
        input_reader = TPFReader(reader)
        vedodo_buffer = VedodoReader(reader).convert_to_class()

        # Check if data has been provided to continue with the validation
        if len(input_reader.data.timestamp) or len(vedodo_buffer.buffer):
            tpf_df = input_reader.data.as_plain_df
            tpf_df = tpf_df.reset_index()
            t7_df = pd.DataFrame(vedodo_buffer.buffer)

            # Check that every timestamp that is present in the TPF output is matching the one provided by T7.
            if tpf_df.timestamp.equals(t7_df.timestamp):
                test_result = fc.PASS
            # Otherwise test will fail
            else:
                # Create a detailed table to show timeframe failing and the corresponding values
                test_result = fc.FAIL
                matching_data = pd.DataFrame(tpf_df.timestamp == t7_df.timestamp)
                failed_cycles = matching_data.loc[~matching_data.timestamp].index
                tpf_failing = tpf_df.filter(items=failed_cycles, axis=0).timestamp
                t7_failing = t7_df.filter(items=failed_cycles, axis=0).timestamp
                fig = go.Figure(
                    data=[
                        go.Table(
                            header=dict(values=["Cycle count", "TPF output", "T7 timestamp"]),
                            cells=dict(values=[failed_cycles, tpf_failing, t7_failing]),
                        )
                    ]
                )
                plot_titles.append("Test Fail report for not matching timestamps")
                plots.append(fig)
                remarks.append("")

            # Add a summary plot with offset behaviour along the rrec
            fig = go.Figure(
                data=[
                    go.Scatter(
                        x=tpf_df.index, y=(tpf_df.timestamp - t7_df.timestamp) / 1e3, mode="lines", name="Offset"
                    )
                ]
            )

            plot_titles.append("TPF timestamp offset ms")
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
    name="CEM-TPF Latency Compensation",
    description="TPF shall provide its signals in the Vehicle coordinate system at T7",
)
class FtTPFOutputAtT7(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFOutputAtT7]


@teststep_definition(
    step_number=1,
    name="CEM-TPF precision rate",
    description=f"""TPF To check if EnvironmentFusion Precision rate matches or exceeds
                {ConstantsCem.TPF_PRECISION_RATE}""",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFPrecisionRate(TestStep):
    """TestStep for TPF Precision Rate, utilizing a custom report."""

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
        input_reader = TPFReader(reader)
        df = input_reader.data.as_plain_df
        vedodo_buffer = VedodoReader(reader).convert_to_class()
        ground_truth = pd.read_hdf(os.path.dirname(__file__) + "\\" + GroundTruthTpf.tpf_gt_file[0])

        tpf_metrics_helper = TPFMetricsHelper(vedodo_buffer, ground_truth)

        # Find ts where there must be data in the output
        df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
        processing_tolerance = ConstantsCem.CYCLE_PERIOD_TIME_MS * ConstantsCem.NUM_OF_CYCLES_FOR_OUTPUT * 1e3
        object_ids = df.loc[:, df.columns.str.startswith(("objects.id", "timestamp"))]
        object_ids.set_index("timestamp", inplace=True)
        first_output_ts = object_ids.loc[(object_ids != 0).any(axis=1)].index.min() + processing_tolerance

        # Select data from the first output available
        input_reader.data = input_reader.data.loc[input_reader.data.timestamp > first_output_ts]

        tpfData = input_reader.convert_to_class()

        if input_reader.number_of_objects > 0:
            failed = 0
            precision_rate_list = []
            associated_objects = []
            for tpf_timeframe in tpfData:
                metrics = tpf_metrics_helper.calc(tpf_timeframe)
                precision_rate_list.append(metrics["precision_rate"])
                associated_objects.append(metrics["Associated_objects"])
                if metrics["precision_rate"] < ConstantsCem.TPF_PRECISION_RATE:
                    failed += 1

            avg_tpf_precision_rate = np.mean(precision_rate_list)
            if avg_tpf_precision_rate < ConstantsCem.TPF_PRECISION_RATE:
                test_result = fc.FAIL
            else:
                test_result = fc.PASS

            # Average Precision Rate ration table
            source_precision_rate = ["TPF"]
            values_precision_rate = [avg_tpf_precision_rate]
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Source", "Average Precision Rate"]),
                        cells=dict(values=[source_precision_rate, values_precision_rate]),
                    )
                ]
            )
            plot_titles.append("Average Precision Rate rate for TP")
            plots.append(fig)
            remarks.append("")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=[timeframe.timestamp for timeframe in tpfData],
                    y=[timeframe.num_objects for timeframe in tpfData],
                    mode="lines",
                    name="TPF output objects",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[timeframe.timestamp for timeframe in tpfData],
                    y=associated_objects,
                    mode="lines",
                    name="Associated objects",
                )
            )
            plot_titles.append("TPF output objects")
            plots.append(fig)
            remarks.append("")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=[timeframe.timestamp for timeframe in tpfData],
                    y=precision_rate_list,
                    mode="lines",
                    name="Cycle precision rate",
                )
            )
            fig.add_hline(
                y=ConstantsCem.TPF_PRECISION_RATE, line_width=2, line_dash="dash", annotation_text="TPF_PRECISION_RATE"
            )
            fig.update_layout(yaxis_range=[-5, 110], showlegend=True)
            plot_titles.append("Average Precision rate")
            plots.append(fig)
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
    name="CEM-TPF precision rate",
    description=f"""TPF To check if EnvironmentFusion Precision rate matches or exceeds
                {ConstantsCem.TPF_PRECISION_RATE}""",
)
class FtTPFPrecisionRate(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFPrecisionRate]


@teststep_definition(
    step_number=1,
    name="CEM-TPF Measured state check",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFMeasuredStateCheck(TestStep):
    """TestStep for TPF Measured State Check, utilizing a custom report."""

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
        input_reader = TPFReader(reader)
        tpf_data = TPFReader(reader).convert_to_class()
        rtp_data = DynamicObjectDetectionReader(reader).convert_to_class()

        if input_reader.number_of_objects > 0:
            rows = []
            failed = 0
            for tpf_timeframe in tpf_data:
                cnt_tpf_objects = len(tpf_timeframe.dynamic_objects)
                cnt_associated_objects = [0] * cnt_tpf_objects

                for camera, _ in rtp_data.items():
                    rtp_timeframe = FtTPFHelper.get_single_relevant_RTP_frame(rtp_data[camera], tpf_timeframe.timestamp)
                    if rtp_timeframe is not None:
                        association = FtTPFHelper.associate_RTP_To_FTP(
                            tpf_timeframe.dynamic_objects, rtp_timeframe.dynamic_objects
                        )

                        cnt_associated_objects = [
                            cnt_associated_objects[i] + len(association[i]) for i in range(cnt_tpf_objects)
                        ]

                for i, tpf_object in enumerate(tpf_timeframe.dynamic_objects):
                    if tpf_object.state == MaintenanceState.PREDICTED and cnt_associated_objects[i] > 0:
                        failed += 1
                        values = [[tpf_timeframe.timestamp], [tpf_object.state]]
                        rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(data=[go.Table(header=dict(values=["Timestamp", "State"]), cells=dict(values=values))])
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
    name="CEM-TPF Measured state check",
    description="This test checks if the object is observed in one timeframe,"
    "its maintenance state is set to 'MEASURED'",
)
class FtTPFMeasuredStateCheck(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFMeasuredStateCheck]


@teststep_definition(
    step_number=1,
    name="CEM-TPF recall rate",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFRecallRate(TestStep):
    """TestStep for TPF Recall Rate, utilizing a custom report."""

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
        tpf_reader = TPFReader(reader)
        tpfData = tpf_reader.convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()
        ground_truth = pd.read_hdf(os.path.dirname(__file__) + "\\" + GroundTruthTpf.tpf_gt_file[0])

        tpf_metrics_helper = TPFMetricsHelper(vedodo_buffer, ground_truth)

        if tpf_reader.number_of_objects > 0:
            rows = []
            failed = 0
            for tpf_timeframe in tpfData[10:]:
                recall_rate = tpf_metrics_helper.calc(tpf_timeframe)["recall_rate"]
                if recall_rate < ConstantsCem.TPF_RECALL_RATE:
                    failed += 1
                    values = [[tpf_timeframe.timestamp], [recall_rate]]
                    rows.append(values)

            if failed:
                test_result = fc.FAIL
                values = list(zip(*rows))
                fig = go.Figure(
                    data=[go.Table(header=dict(values=["Timestamp", "Recall rate"]), cells=dict(values=values))]
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
    name="CEM-TPF recall rate",
    description=f"""TPF To check if EnvironmentFusion Recall rate matches of exceeds {ConstantsCem.TPF_RECALL_RATE}""",
)
class FtTPFRecallRate(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFRecallRate]


@teststep_definition(
    step_number=1,
    name="CEM-TPF Sensor Contribution",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFSensor(TestStep):
    """TestStep for TPF Sensor, utilizing a custom report."""

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
        tpfData = TPFReader(reader).convert_to_class()
        rtpData = DynamicObjectDetectionReader(reader).convert_to_class()

        for _, timeframe in enumerate(tpfData):
            for camera in DynamicObjectCamera:
                # Get T6 timestamp instead of T7 for the search
                rtp_timeframes = FtTPFHelper.get_relevant_RTP_Frames(rtpData[camera], timeframe.timestamp)
                for rtp_tf in rtp_timeframes:
                    associations = FtTPFHelper.associate_RTP_To_FTP(timeframe.dynamic_objects, rtp_tf.dynamic_objects)
                    for i, _ in enumerate(timeframe.dynamic_objects):
                        if len(associations[i]) > 0:
                            # Check if current camera contribution is set for this FTP
                            pass
                        else:
                            # Check if current camera contribution is not set for this FTP
                            pass

        # test_result = fc.IMPLEMENTATION_NOT_AVAILABLE
        test_result = fc.NOT_AVAILABLE

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
    name="CEM-TPF Sensor Contribution",
    description="This test case is to validate which sensors was used to provide the FTP",
)
class FtTPFSensor(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFSensor]


@teststep_definition(
    step_number=1,
    name="CEM-TPF AL Signal State",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFSigStateOk(TestStep):
    """TestStep for TPF Signal State OK, utilizing a custom report."""

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

        objects_used = 4  # ToDo: Confirm amount of objects used for this test
        # Variable definition
        reader = self.readers[SIGNAL_DATA].signals
        data_df = reader.as_plain_df

        # Load TPF inputs
        input_data = data_df[
            [
                "Front_timestamp",
                "Front_numObjects",
                "Front_objects_eSigStatus",
                "Rear_timestamp",
                "Rear_numObjects",
                "Rear_objects_eSigStatus",
                "Left_timestamp",
                "Left_numObjects",
                "Left_objects_eSigStatus",
                "Right_timestamp",
                "Right_numObjects",
                "Right_objects_eSigStatus",
            ]
        ]
        tpf_inputs_df = input_data.filter(regex="objects_eSigStatus")
        tpf_input_timestamp_df = input_data.filter(regex="timestamp")

        tpf_output_df = data_df[["timestamp", "numObjects"]]

        if len(tpf_inputs_df.columns) < 4:
            test_result = fc.INPUT_MISSING
        else:
            # Get first time when any of the input’s sig_state == OK and find TPF output for it.
            # ToDo: Confirm processing time
            processing_tolerance = ConstantsCem.CYCLE_PERIOD_TIME_MS * ConstantsCem.NUM_OF_CYCLES_FOR_OUTPUT * 1e3
            first_section_end = tpf_inputs_df[tpf_inputs_df.isin([fc.AL_SIG_STATE_OK]).any(axis=1)].index[0]
            first_section_end_time = tpf_input_timestamp_df.iloc[first_section_end].min()
            tpf_output_closest = tpf_output_df.loc[tpf_output_df.timestamp > first_section_end_time].index[0]

            # Get timestamp where sig_state changes to OK = (1) for all the cameras.
            second_section_start = first_section_end_time + processing_tolerance
            output_closest_second_start = tpf_output_df.loc[tpf_output_df.timestamp > second_section_start].index[0]
            second_section_end = tpf_inputs_df[tpf_inputs_df.isin([fc.AL_SIG_STATE_OK]).all(axis=1)].index[0]
            second_section_end_time = tpf_input_timestamp_df.iloc[second_section_end].min()
            tpf_output_closest_next = tpf_output_df.loc[tpf_output_df.timestamp > second_section_end_time].index[0]

            failing_section = []
            expected_result = []
            result_provided = []
            section_range = []

            # Confirm there is no TPF output at first section
            if max(tpf_output_df.loc[:tpf_output_closest, "numObjects"]) == 0:
                first_section_result = True
            else:
                first_section_result = False
                failing_section.append("First scenario")
                expected_result.append("numObjects = 0")
                result_provided.append(max(tpf_output_df.loc[:tpf_output_closest, "numObjects"]))
                section_range.append(
                    f"{tpf_output_df.timestamp.iat[0]} - " f"{tpf_output_df.timestamp[tpf_output_closest]}"
                )

            # Starting from next timestamp after one obtained in step 2.1 through the whole measurement.
            # Confirm TPF output provide > 0 and <= 4 objects.
            outputs_from_valid_inputs = tpf_output_df.loc[output_closest_second_start:, "numObjects"]
            if min(outputs_from_valid_inputs) > 0 and max(outputs_from_valid_inputs) <= objects_used:
                second_section_result = True
            else:
                second_section_result = False
                failing_section.append("Second scenario")
                expected_result.append(f"0 < numObjects <= {objects_used}")
                result_provided.append(f"min: {min(outputs_from_valid_inputs)} max: {max(outputs_from_valid_inputs)}")
                section_range.append(
                    f"{tpf_output_df.timestamp[output_closest_second_start]} - " f"{tpf_output_df.timestamp.iat[-1]}"
                )

            # Test will pass if all sections pass
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
                                    "TPF expected Objects",
                                    "TPF Objects provided",
                                    "Output section range",
                                ]
                            ),
                            cells=dict(values=[failing_section, expected_result, result_provided, section_range]),
                        )
                    ]
                )
                plot_titles.append("Test Fail Summary")
                plots.append(fig)
                remarks.append("")

            # Add a summary plot with signals behaviour along the rrec
            fig = go.Figure(
                data=[
                    go.Scatter(x=tpf_output_df.timestamp, y=tpf_output_df.numObjects, mode="lines", name="TPF output"),
                    go.Scatter(
                        x=tpf_input_timestamp_df.timestamp_Front,
                        y=tpf_inputs_df.sigState_Front,
                        mode="lines",
                        name="sigState_Front",
                    ),
                    go.Scatter(
                        x=tpf_input_timestamp_df.timestamp_Rear,
                        y=tpf_inputs_df.sigState_Rear,
                        mode="lines",
                        name="sigState_Rear",
                    ),
                    go.Scatter(
                        x=tpf_input_timestamp_df.timestamp_Left,
                        y=tpf_inputs_df.sigState_Left,
                        mode="lines",
                        name="sigState_Left",
                    ),
                    go.Scatter(
                        x=tpf_input_timestamp_df.timestamp,
                        y=tpf_inputs_df.sigState,
                        mode="lines",
                        name="sigState_Right",
                    ),
                ]
            )

            fig.add_vrect(
                x0=tpf_output_df.timestamp.iat[0],
                x1=tpf_output_df.timestamp[tpf_output_closest],
                fillcolor="#BBDEFB",
                layer="below",
            )

            fig.add_vrect(
                x0=tpf_output_df.timestamp[output_closest_second_start],
                x1=tpf_output_df.timestamp[tpf_output_closest_next],
                fillcolor="#BBDEFB",
                layer="below",
            )

            fig.add_vrect(
                x0=tpf_output_df.timestamp[tpf_output_closest_next],
                x1=tpf_output_df.timestamp.iat[-1],
                fillcolor="#BBDEFB",
                layer="below",
            )

            plot_titles.append(f"Test {test_result.lower()} report")
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
    name="CEM-TPF Sensor Contribution",
    description="This test case is to validate if TPF only process input signals "
    "if their signal state is AL_SIG_STATE_OK",
)
class FtTPFSigStateOk(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFSigStateOk]


@teststep_definition(
    step_number=1,
    name="CEM-TPF X and Y Velocity Accuracy",
    description="This test checks if CEM-LSM provides the velocity in x and y direction of the dynamic objects "
    "with following accuracy values: "
    "Accuracy x/y (max. dist)"
    "+/- {AP_E_DYN_OBJ_VELOCITY_ACCURACY_20_5_mps} ( < 20m, >5m)"
    "+/- {AP_E_DYN_OBJ_VELOCITY_ACCURACY_5_1_mps} (<=5m, >1m)"
    "+/- {AP_E_DYN_OBJ_VELOCITY_ACCURACY_1_mps} (<= 1m)",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtTPFXYVelAcc(TestStep):
    """TestStep for TPF XY Velocity Accuracy, utilizing a custom report."""

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

        test_result = fc.NOT_ASSESSED
        plot_titles, plots, remarks = rep([], 3)

        reader = self.readers[SIGNAL_DATA].signals
        tpf_data = TPFReader(reader).convert_to_class()
        vedodo_buffer = VedodoReader(reader).convert_to_class()
        ground_truth = pd.read_hdf(os.path.dirname(__file__) + "\\" + GroundTruthTpf.tpf_gt_file[0])
        rtp_data = DynamicObjectDetectionReader(reader).convert_to_class()

        associator = TpfFtp2GtAssociator(vedodo_buffer, ground_truth)

        rtp_satisfy_dynamics_acc_1m = 0
        rtp_satisfy_dynamics_acc_5m = 0
        rtp_satisfy_dynamics_acc_20m = 0
        ftp_satisfy_dynamics_vx_acc_1m = 0
        ftp_satisfy_dynamics_vy_acc_1m = 0
        ftp_satisfy_dynamics_vx_acc_5m = 0
        ftp_satisfy_dynamics_vy_acc_5m = 0
        ftp_satisfy_dynamics_vx_acc_20m = 0
        ftp_satisfy_dynamics_vy_acc_20m = 0
        dynamics_vx_acc_ratio_1m = 0
        dynamics_vy_acc_ratio_1m = 0
        dynamics_vx_acc_ratio_5m = 0
        dynamics_vy_acc_ratio_5m = 0
        dynamics_vx_acc_ratio_20m = 0
        dynamics_vy_acc_ratio_20m = 0

        for tpf_timeframe in tpf_data[20:]:
            ftp_association = associator.associate(tpf_timeframe)
            gts = associator.get_gt_at_timeframe(tpf_timeframe.timestamp)
            inv_ftp_association = {v: k for k, v in ftp_association.items()}

            for camera, _ in rtp_data.items():
                rtp_timeframe = FtTPFHelper.get_single_relevant_RTP_frame(rtp_data[camera], tpf_timeframe.timestamp)
                if rtp_timeframe is None:
                    continue
                rtp_association = associator.associate(rtp_timeframe)
                for rtp_id, gt_id in rtp_association.items():
                    rtp = FtTPFHelper.get_Tp_by_id(rtp_timeframe.dynamic_objects, rtp_id)
                    gt = gts[gt_id]
                    if abs(rtp.center_x - gt["x"]) <= 1:
                        rtp_satisfy_dynamics_acc_1m += 1
                    elif 1 < abs(rtp.center_x - gt["x"]) <= 5:
                        rtp_satisfy_dynamics_acc_5m += 1
                    elif 5 < abs(rtp.center_x - gt["x"]) < 20:
                        rtp_satisfy_dynamics_acc_20m += 1
                    if gt_id in inv_ftp_association:
                        ftp = FtTPFHelper.get_Tp_by_id(tpf_timeframe.dynamic_objects, inv_ftp_association[gt_id])
                        ftp_vx_acc = abs(ftp.velocity_x - gt["vx"])
                        ftp_vy_acc = abs(ftp.velocity_y - gt["vy"])
                        # +/- {AP_E_DYN_OBJ_VELOCITY_ACCURACY_1_mps} (<= 1m)
                        if abs(rtp.center_x - gt["x"]) <= 1:
                            if ftp_vx_acc <= ConstantsCem.AP_E_DYN_OBJ_VELOCITY_ACCURACY_1_MPS:
                                ftp_satisfy_dynamics_vx_acc_1m += 1
                            if ftp_vy_acc <= ConstantsCem.AP_E_DYN_OBJ_VELOCITY_ACCURACY_1_MPS:
                                ftp_satisfy_dynamics_vy_acc_1m += 1
                        # +/- {AP_E_DYN_OBJ_VELOCITY_ACCURACY_5_1_mps} (<=5m, >1m)
                        elif 1 < abs(rtp.center_x - gt["x"]) <= 5:
                            if ftp_vx_acc <= ConstantsCem.AP_E_DYN_OBJ_VELOCITY_ACCURACY_5_1_MPS:
                                ftp_satisfy_dynamics_vx_acc_5m += 1
                            if ftp_vy_acc <= ConstantsCem.AP_E_DYN_OBJ_VELOCITY_ACCURACY_5_1_MPS:
                                ftp_satisfy_dynamics_vy_acc_5m += 1
                        # +/- {AP_E_DYN_OBJ_VELOCITY_ACCURACY_20_5_mps} ( < 20m, >5m)
                        elif 5 < abs(rtp.center_x - gt["x"]) < 20:
                            if ftp_vx_acc <= ConstantsCem.AP_E_DYN_OBJ_VELOCITY_ACCURACY_20_5_MPS:
                                ftp_satisfy_dynamics_vx_acc_20m += 1
                            if ftp_vy_acc <= ConstantsCem.AP_E_DYN_OBJ_VELOCITY_ACCURACY_20_5_MPS:
                                ftp_satisfy_dynamics_vy_acc_20m += 1

        if rtp_satisfy_dynamics_acc_1m > 0:
            dynamics_vx_acc_ratio_1m = ftp_satisfy_dynamics_vx_acc_1m / rtp_satisfy_dynamics_acc_1m
            dynamics_vy_acc_ratio_1m = ftp_satisfy_dynamics_vy_acc_1m / rtp_satisfy_dynamics_acc_1m
        if rtp_satisfy_dynamics_acc_5m > 0:
            dynamics_vx_acc_ratio_5m = ftp_satisfy_dynamics_vx_acc_5m / rtp_satisfy_dynamics_acc_5m
            dynamics_vy_acc_ratio_5m = ftp_satisfy_dynamics_vy_acc_5m / rtp_satisfy_dynamics_acc_5m
        if rtp_satisfy_dynamics_acc_20m > 0:
            dynamics_vx_acc_ratio_20m = ftp_satisfy_dynamics_vx_acc_20m / rtp_satisfy_dynamics_acc_20m
            dynamics_vy_acc_ratio_20m = ftp_satisfy_dynamics_vy_acc_20m / rtp_satisfy_dynamics_acc_20m

        if (
            dynamics_vx_acc_ratio_1m < 1
            or dynamics_vx_acc_ratio_5m < 1
            or dynamics_vx_acc_ratio_20m < 1
            or dynamics_vy_acc_ratio_1m < 1
            or dynamics_vy_acc_ratio_5m < 1
            or dynamics_vy_acc_ratio_20m < 1
        ):
            test_result = fc.FAIL
        else:
            test_result = fc.PASS
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=["VX accuracy", "VY accuracy", "Max dist", "Accuracy Threshold"]),
                    cells=dict(
                        values=[
                            [
                                dynamics_vx_acc_ratio_1m * 100,
                                dynamics_vx_acc_ratio_5m * 100,
                                dynamics_vx_acc_ratio_20m * 100,
                            ],
                            [
                                dynamics_vy_acc_ratio_1m * 100,
                                dynamics_vy_acc_ratio_5m * 100,
                                dynamics_vy_acc_ratio_20m * 100,
                            ],
                            ["(<= 1m)", "(<=5m, >1m)", "( < 20m, >5m)"],
                            [
                                ConstantsCem.AP_E_DYN_OBJ_VELOCITY_ACCURACY_1_MPS,
                                ConstantsCem.AP_E_DYN_OBJ_VELOCITY_ACCURACY_5_1_MPS,
                                ConstantsCem.AP_E_DYN_OBJ_VELOCITY_ACCURACY_20_5_MPS,
                            ],
                        ]
                    ),
                )
            ]
        )
        plot_titles.append(f"Test {test_result} report")
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
    name="CEM-TPF X and Y Velocity Accuracy",
    description="This test case checks if CEM-LSM provides the velocity in x and y direction of the dynamic objects "
    "with following accuracy values: "
    "Accuracy x/y (max. dist)"
    "+/- {AP_E_DYN_OBJ_VELOCITY_ACCURACY_20_5_mps} ( < 20m, >5m)"
    "+/- {AP_E_DYN_OBJ_VELOCITY_ACCURACY_5_1_mps} (<=5m, >1m)"
    "+/- {AP_E_DYN_OBJ_VELOCITY_ACCURACY_1_mps} (<= 1m)",
)
class FtTPFXYVelAcc(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtTPFXYVelAcc]
