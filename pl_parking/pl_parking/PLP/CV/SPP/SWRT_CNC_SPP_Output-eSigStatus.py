#!/usr/bin/env python3
"""Validation of Test Case SWRT_CNC_SPP_Output-eSigStatus."""

import logging
import os
import sys

import pandas as pd

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, get_color
from pl_parking.PLP.CV.SPP.constants import SensorSource, SppSigStatus
from pl_parking.PLP.CV.SPP.ft_helper import SPPPreprocessor, SPPSignals

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_pre_processor,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

__author__ = "<uib11434>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "testcase_42082"


@teststep_definition(
    step_number=1,
    name="SWRT_CNC_SPP_Output-eSigStatus",
    description="Check if SPP function provide as output an eSigStatus field.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SPPSignals)
@register_pre_processor(alias="check_signals", pre_processor=SPPPreprocessor)
class SppOutputSigStatusTestStep(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()
        self.test_result = fc.INPUT_MISSING
        self.sig_sum = None

    def process(self):
        """Process the simulated files."""
        _log.debug("Starting processing...")

        # Update the details from the results page with the needed information. All the information from
        # self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Initializing the result with data nok
        self.result.measured_result = DATA_NOK

        # Create empty lists for titles, plots and remarks, if they are needed.
        # Plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        # Initializing the dictionary with data for final evaluation table
        signal_summary = {}

        cameras = {
            SensorSource.SPP_FC_DATA: DATA_NOK,
            SensorSource.SPP_LSC_DATA: DATA_NOK,
            SensorSource.SPP_RC_DATA: DATA_NOK,
            SensorSource.SPP_RSC_DATA: DATA_NOK,
        }

        cameras_from_preprocessor, reader_df = self.pre_processors["check_signals"]
        for camera, pre_processor_result in cameras_from_preprocessor.items():
            cam_evaluation = " ".join(
                f"Signal pSppPolylines.sSigHeader.eSigStatus is provided with one of the following values: "
                f"{SppSigStatus.AL_SIG_STATE_INIT}, {SppSigStatus.AL_SIG_STATE_OK}, "
                f"{SppSigStatus.AL_SIG_STATE_INVALID}".split()
            )

            # get the availability of the signals
            signals_available, list_of_failed = pre_processor_result[0]

            if signals_available:
                list_of_failed = [
                    (mts_timestamp, polyline_sig_status)
                    for mts_timestamp, polyline_sig_status in self.loop_signals_df(reader_df, camera)
                    if polyline_sig_status
                    not in [
                        SppSigStatus.AL_SIG_STATE_INIT,
                        SppSigStatus.AL_SIG_STATE_OK,
                        SppSigStatus.AL_SIG_STATE_INVALID,
                    ]
                ]
                if len(list_of_failed) > 0:
                    cam_test_result = fc.FAIL
                    # create an evaluation text for the moment when the test is failed
                    cam_evaluation = " ".join(
                        f"The evaluation is FAILED in {len(list_of_failed)} cases. "
                        f"Signal pSppPolylines.sSigHeader.eSigStatus is provided with a wrong a value "
                        f"{list_of_failed[0][1]} at frame {list_of_failed[0][0]}".split()
                    )
                else:
                    cam_test_result = fc.PASS
                cameras.update({camera: cam_test_result})

            else:
                cam_evaluation = " ".join(
                    "Signal pSppPolylines.sSigHeader.eSigStatus is not available in the bsig file. ".split()
                )

            signal_summary[camera] = cam_evaluation

        remark = " ".join(
            "Check that SPP function provide as output an eSigStatus field that describes the readiness of the system "
            "for the detection of the boundaries.".split()
        )

        # The signal summary and observations will be converted to pandas
        # and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(
            signal_summary=signal_summary,
            table_remark=remark,
        )
        plots.append(self.sig_sum)

        if any(camera_test_result == DATA_NOK for camera_test_result in cameras.values()):
            self.test_result = fc.INPUT_MISSING
            self.result.measured_result = DATA_NOK
        elif any(camera_test_result == fc.FAIL for camera_test_result in cameras.values()):
            self.test_result = fc.FAIL
            self.result.measured_result = FALSE
        elif all(camera_test_result == fc.PASS for camera_test_result in cameras.values()):
            self.test_result = fc.PASS
            self.result.measured_result = TRUE

        result_df = {
            "Verdict": {"value": self.test_result.title(), "color": get_color(self.test_result)},
            fc.REQ_ID: ["1565875"],
            fc.TESTCASE_ID: ["42082"],
            fc.TEST_DESCRIPTION: ["Check if SPP function provide as output an eSigStatus field"],
        }

        self.result.details["Additional_results"] = result_df

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)

    @staticmethod
    def loop_signals_df(df: pd.DataFrame, camera):
        """
        Loops over the signals dataframe.

        :param df:
        :param camera:
        :return: mts_timestamp value, polylines_sig_status value
        """
        if camera is SensorSource.SPP_FC_DATA:
            for mts_timestamp, polylines_sig_status in zip(
                df[SPPSignals.Columns.MTS_TS].values, df[SPPSignals.Columns.FC_POLYLINES_SIG_STATUS].values
            ):
                yield mts_timestamp, polylines_sig_status
        elif camera is SensorSource.SPP_LSC_DATA:
            for mts_timestamp, polylines_sig_status in zip(
                df[SPPSignals.Columns.MTS_TS].values, df[SPPSignals.Columns.LSC_POLYLINES_SIG_STATUS].values
            ):
                yield mts_timestamp, polylines_sig_status
        elif camera is SensorSource.SPP_RC_DATA:
            for mts_timestamp, polylines_sig_status in zip(
                df[SPPSignals.Columns.MTS_TS].values, df[SPPSignals.Columns.RC_POLYLINES_SIG_STATUS].values
            ):
                yield mts_timestamp, polylines_sig_status
        elif camera is SensorSource.SPP_RSC_DATA:
            for mts_timestamp, polylines_sig_status in zip(
                df[SPPSignals.Columns.MTS_TS].values, df[SPPSignals.Columns.RSC_POLYLINES_SIG_STATUS].values
            ):
                yield mts_timestamp, polylines_sig_status


@verifies("L3_SPP_1565875")
@testcase_definition(
    name="SWRT_CNC_SPP_Output-eSigStatus",
    description=(
        "This test verifies if SPP function provide as output an eSigStatus field that describes the readiness "
        "of the system for the detection of the boundaries."
    ),
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2F"
    "jazz.conti.de%2Frm4%2Fresources%2FBI_K6ddsF-nEe6hyY-R-i-gng&componentURI=https%3A%2F%2Fjazz.conti.de%2F"
    "rm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_Z9LhwDK_Ee6mrdm2_agUYg&oslc.configuration="
    "https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17100",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SppOutputSigStatus(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SppOutputSigStatusTestStep,
        ]
