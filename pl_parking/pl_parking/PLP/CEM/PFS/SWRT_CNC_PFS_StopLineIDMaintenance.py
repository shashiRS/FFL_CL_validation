"""StopLines ID Maintenance Test."""

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

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants, ConstantsCemInput
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PclDelimiterReader
from pl_parking.PLP.CEM.inputs.input_CemSLReader import SLDetectionReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera

SIGNAL_DATA = "PFS_SL_ID_Maintenance"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS SL ID Maintenance",
    description="This test case checks if the same ID is given for a Stop Lines detection"
    "which is received in the current cycle and is associated to a Stop Lines"
    "which PFS provided in the previous cycle with a unique ID.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtSLIdMaintenance(TestStep):
    """StopLines ID Maintenance Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarsk based
        on the evaluation results
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}
        evaluation = []

        try:
            reader = self.readers[SIGNAL_DATA].signals
            pcl_data = PclDelimiterReader(reader).convert_to_class()
            sl_detection_data = SLDetectionReader(reader).convert_to_class()
            vedodo_buffer = VedodoReader(reader).convert_to_class()

            # TO DO: CEM Stop Line signals might change later and should be corrected or added in Common_ft_helper.
            data_df = reader.as_plain_df
            data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
            pcl_type = data_df.loc[:, data_df.columns.str.startswith("delimiterType")]

            if ConstantsCemInput.SLEnum in pcl_type.values:
                rows = []
                failed = 0
                evaluated_cycles = 0
                for index, curTimeframe in enumerate(pcl_data):
                    if index == 0:
                        continue

                    prev_time_frame = pcl_data[index - 1]
                    relative_motion_output = vedodo_buffer.calc_relative_motion(
                        curTimeframe.timestamp, prev_time_frame.timestamp
                    )

                    transformed_prev_sl = [
                        FtPclHelper.transform_pcl(wl, relative_motion_output) for wl in prev_time_frame.stop_line_array
                    ]

                    sl_ts_index = [
                        FtPclHelper.get_PMD_timeframe_index(
                            curTimeframe.timestamp, prev_time_frame.timestamp, sl_detection_data[camera]
                        )
                        for camera in PMDCamera
                    ]

                    sl_timeframes = [
                        sl_detection_data[camera][sl_ts_index[int(camera)]]
                        for camera in PMDCamera
                        if sl_ts_index[int(camera)] is not None
                    ]

                    #
                    updated_sl = FtPclHelper.get_marker_with_associated_input(
                        transformed_prev_sl, sl_timeframes, AssociationConstants.SL_ASSOCIATION_RADIUS
                    )

                    associations = FtPclHelper.associate_PCL_list(
                        curTimeframe.stop_line_array, updated_sl, AssociationConstants.SL_ASSOCIATION_RADIUS
                    )

                    for prev_ixd, curr_index in associations.items():
                        evaluated_cycles += 1
                        if updated_sl[prev_ixd].delimiter_id != curTimeframe.stop_line_array[curr_index].delimiter_id:
                            failed += 1
                            values = [
                                [curTimeframe.timestamp],
                                [updated_sl[prev_ixd].delimiter_id],
                                [curTimeframe.stop_line_array[curr_index].delimiter_id],
                            ]
                            rows.append(values)

                if failed:
                    test_result = fc.FAIL
                    values = list(zip(*rows))
                    fig = go.Figure(
                        data=[
                            go.Table(
                                header=dict(values=["Timestamp", "Prev Slot ID", "Curr Slot ID"]),
                                cells=dict(values=values),
                            )
                        ]
                    )
                    plot_titles.append("Test Fail report")
                    plots.append(fig)
                    remarks.append("")

                    fig0 = go.Figure(
                        data=[go.Table(header=dict(values=["Evaluated cycles"]), cells=dict(values=[evaluated_cycles]))]
                    )
                    plot_titles.append("Number of evaluated cycles")
                    plots.append(fig0)
                    remarks.append("")
                else:
                    test_result = fc.PASS

            else:
                test_result = fc.INPUT_MISSING
        except KeyError as err:
            test_result = fc.FAIL
            evaluation = "Key Error " + str(err)
            signal_summary["Stoplines_UniquesID"] = evaluation

        if evaluation is not None:
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=["Signal Evaluation", "Summary"]),
                        cells=dict(values=[list(signal_summary.keys()), list(signal_summary.values())]),
                    )
                ]
            )

            plot_titles.append("Signal Evaluation")
            plots.append(fig)
            remarks.append("PFS Evaluation")

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["2260076"],
            fc.TESTCASE_ID: ["64808"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test case checks If a Stop Lines detection is received in the current cycle and is "
                "associated to a Stop Lines which PFS provided in the previous cycle with a unique ID, "
                "PFS shall provide the same ID for this updated Stop Lines in the current cycle."
            ],
            fc.TEST_RESULT: [test_result],
        }

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

        self.result.details["Additional_results"] = result_df


@verifies("2260076")
@testcase_definition(
    name="SWRT_CNC_PFS_StopLineIDMaintenance",
    description="Stop Lines Unique ID",
)
class FtSLIdMaintenance(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSLIdMaintenance]
