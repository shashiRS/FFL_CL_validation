"""Parking Markers ID Maintenance Test."""

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


import tempfile
from pathlib import Path

import plotly.graph_objects as go
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import CemSignals, MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.constants import AssociationConstants
from pl_parking.PLP.CEM.ft_pcl_helper import FtPclHelper
from pl_parking.PLP.CEM.inputs.input_CemPclReader import PclDelimiterReader
from pl_parking.PLP.CEM.inputs.input_CemVedodoReader import VedodoReader
from pl_parking.PLP.CEM.inputs.input_PmdReader import PMDCamera, PMDReader

SIGNAL_DATA = "PFS_PCL_ID_Maintenance"

example_obj = CemSignals()


@teststep_definition(
    step_number=1,
    name="CEM PFS PCL ID Maintenance",
    description="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, CemSignals)
class TestStepFtPCLMaintID(TestStep):
    """Parking Markers ID Maintenance Test."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step"""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based
        on the evaluation results
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
        pcl_type = data_df.loc[:, data_df.columns.str.startswith("Cem_pcl_delimiterId")]

        if not pcl_type.empty:
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

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1530462"],
            fc.TESTCASE_ID: ["38842"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "This test checks that EnvironmentFusion maintains the identifier of each parking marker"
                "if a parking marker detection is received in the current timeframe and can be associated"
                "to a parking marker already received in previous time frames."
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


@verifies("1530462")
@testcase_definition(
    name="SWRT_CNC_PFS_ParkingMarkersIDMaintenance",
    description="This test checks that EnvironmentFusion maintains the identifier of each parking marker"
    "if a parking marker detection is received in the current timeframe and can be associated"
    "to a parking marker already received in previous time frames.",
)
class FtPCLMaintID(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtPCLMaintID]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.
    """
    # test_bsigs = r'D:\Rrec_Ext_Bsigs\Recordings\trjpla\exported_file__D2024_01_09_T13_51_40.bsig'
    # test_bsigs = r"D:\Rrec_Ext_Bsigs\Bsig_Output\carpc_wheelstopper\2022.08.04_at_13.29.33_svu-mi5_149.bsig"
    test_bsigs = r"D:\Rrec_Ext_Bsigs\Bsig_Output\R4 Bsigs\PFS_ergs\PFS_3ODSlot_PCL_WS_WL_SL_PC.erg"
    debug(
        FtPCLMaintID,
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
