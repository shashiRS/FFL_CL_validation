#!/usr/bin/env python3
"""Root cause analysis for Slot Offer test."""
import json
import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
from time import time as start_time

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
from tsf.io.signals import SignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport

__author__ = "BA ADAS ENP SIMU KPI"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "ROOT_CAUSE_SO"
now_time = start_time()


class StoreStepResults:
    """Initializes variables for multiple steps and provides a method
    to check their status and return corresponding results and color codes.
    """

    def __init__(self):
        """Initialize the test steps results"""
        self.step_1 = fc.INPUT_MISSING
        self.step_2 = fc.INPUT_MISSING
        self.step_3 = fc.INPUT_MISSING
        self.step_4 = fc.INPUT_MISSING
        self.step_5 = fc.INPUT_MISSING
        self.step_6 = fc.INPUT_MISSING
        self.step_7 = fc.INPUT_MISSING
        self.step_8 = fc.INPUT_MISSING

    def check_result(self):
        """
        The function `check_result` checks the status of multiple steps and returns a corresponding result and color code.
        :return: The `check_result` method is returning a tuple with two values. The first value is one of the constants
        `fc.PASS`, `fc.INPUT_MISSING`, `fc.NOT_ASSESSED`, or `fc.FAIL` based on the conditions checked in the method. The
        second value is a color code represented as a string.
        """
        if (
            self.step_1 == fc.PASS
            and self.step_2 == fc.PASS
            and self.step_3 == fc.PASS
            and self.step_4 == fc.PASS
            and self.step_5 == fc.PASS
            and self.step_6 == fc.PASS
            and self.step_7 == fc.PASS
            and self.step_8 == fc.PASS
        ):
            return fc.PASS, "#28a745"
        elif (
            self.step_1 == fc.INPUT_MISSING
            or self.step_2 == fc.INPUT_MISSING
            or self.step_3 == fc.INPUT_MISSING
            or self.step_4 == fc.INPUT_MISSING
            or self.step_5 == fc.INPUT_MISSING
            or self.step_6 == fc.INPUT_MISSING
            or self.step_7 == fc.INPUT_MISSING
            or self.step_8 == fc.INPUT_MISSING
        ):
            return fc.INPUT_MISSING, "rgb(33,39,43)"
        elif (
            self.step_1 == fc.NOT_ASSESSED
            or self.step_2 == fc.NOT_ASSESSED
            or self.step_3 == fc.NOT_ASSESSED
            or self.step_4 == fc.NOT_ASSESSED
            or self.step_5 == fc.NOT_ASSESSED
            or self.step_6 == fc.NOT_ASSESSED
            or self.step_7 == fc.NOT_ASSESSED
            or self.step_8 == fc.NOT_ASSESSED
        ):
            return fc.NOT_ASSESSED, "rgb(129, 133, 137)"
        else:
            # self.case_result == fc.FAIL
            return fc.FAIL, "#dc3545"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        sg_time = "TimeStamp"
        NUMBER_OF_POINTS = "Number Of Points"
        NUMBER_OF_ECHOS = "Number Of Echos"
        NUMBER_OF_LINES_FC = "Number Of Lines FC"
        NUMBER_OF_LINES_LSC = "Number Of Lines LSC"
        NUMBER_OF_LINES_RC = "Number Of Lines RC"
        NUMBER_OF_LINES_RSC = "Number Of Lines RSC"

        NUMBER_OF_DELIMITERS = "Number Of Delimiters"
        NUMBER_OF_SLOTS = "Number Of Slots"
        NUMBER_OF_OBJECTS = "Number Of Objects"
        NUMBER_OF_PARKMARK = "Number Of Parking Marks"
        NUMBER_OF_STATOBJ = "Number Of Static Objects"
        NUMBER_OF_VALID_PB = "Number Of Valid Parking Boxes"
        NUMBER_OF_VALID_POSES = "Number Of Valid Poses"
        SELECTED_PB_ID = "SelectedPB-ID"
        SCREEN_NU = "Screen_nu"
        PARK_SPACES = "Park_spaces"
        VELOCITY = "Velocity"
        HMI_PS_RIGHT_0 = "parkingSpaces.right.scanned_0"
        HMI_PS_RIGHT_1 = "parkingSpaces.right.scanned_1"
        HMI_PS_RIGHT_2 = "parkingSpaces.right.scanned_2"
        HMI_PS_RIGHT_3 = "parkingSpaces.right.scanned_3"
        HMI_PS_LEFT_0 = "parkingSpaces.left.scanned_0"
        HMI_PS_LEFT_1 = "parkingSpaces.left.scanned_1"
        HMI_PS_LEFT_2 = "parkingSpaces.left.scanned_2"
        HMI_PS_LEFT_3 = "parkingSpaces.left.scanned_3"
        PATH_FOUND = "Any Path Found"
        FAIL_REASON = "Fail Reason"
        sg_time_m7 = "TimeStamp_M7"
        SOFTWARE_MAJOR = "SOFTWARE_MAJOR"
        SOFTWARE_MINOR = "SOFTWARE_MINOR"
        SOFTWARE_PATCH = "SOFTWARE_PATCH"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["ADC5xx_Device", "ADAS_CAN", "MTA_ADC5", "AP_Conti_CAN"]

        self._properties = {
            self.Columns.NUMBER_OF_POINTS: [
                ".USP_DATA.SpuUsProcessingPointListOutput.numberOfPoints",
                ".US_PROCESSING_DATA.UsProcessingPointListOutput.numberOfPoints",
            ],
            self.Columns.NUMBER_OF_ECHOS: [
                ".USP_DATA.SpuUsProcessingEchoOutput.numEchoes",
                ".US_PROCESSING_DATA.UsProcessingEchoOutput.numEchoes",
            ],
            self.Columns.NUMBER_OF_LINES_FC: [
                ".PMSD_FC_DATA.PmsdParkingLinesOutputFc.numberOfLines",
                ".PMSD_FC_DATA.ParkingLines.numberOfLines",
            ],
            self.Columns.NUMBER_OF_LINES_LSC: [
                ".PMSD_LSC_DATA.PmsdParkingLinesOutputLsc.numberOfLines",
                ".PMSD_LSC_DATA.ParkingLines.numberOfLines",
            ],
            self.Columns.NUMBER_OF_LINES_RC: [
                ".PMSD_RC_DATA.PmsdParkingLinesOutputRc.numberOfLines",
                ".PMSD_RC_DATA.ParkingLines.numberOfLines",
            ],
            self.Columns.NUMBER_OF_LINES_RSC: [
                ".PMSD_RSC_DATA.PmsdParkingLinesOutputRsc.numberOfLines",
                ".PMSD_RSC_DATA.ParkingLines.numberOfLines",
            ],
            self.Columns.NUMBER_OF_DELIMITERS: [
                ".CEM_EM_DATA.AUPDF_ParkingDelimiters.numberOfDelimiters",
                # ".CEM200_AUPDF_DATA.ParkingDelimiters.numberOfDelimiters",
                "MTA_ADC5.CEM200_PFS_DATA.m_PclOutput.numberOfDelimiters",
            ],
            self.Columns.NUMBER_OF_SLOTS: [
                ".CEM_EM_DATA.AUPDF_ParkingSlots.numberOfSlots",
                # ".CEM200_AUPDF_DATA.ParkingSlots.numberOfSlots",
                "MTA_ADC5.CEM200_PFS_DATA.m_PsdOutput.numberOfSlots",
            ],
            self.Columns.NUMBER_OF_OBJECTS: [
                ".CEM_EM_DATA.AUPDF_DynamicObjects.numberOfObjects",
                # ".CEM200_AUPDF_DATA.DynamicObjects.numberOfObjects",
                "MTA_ADC5.CEM200_TPF2_DATA.m_tpObjectList.numberOfObjects",

            ],
            self.Columns.NUMBER_OF_PARKMARK: [
                ".EM_DATA.EmApEnvModelPort.numberOfParkMarkings_u8",
                ".SI_DATA.m_environmentModelPort.numberOfParkMarkings_u8",
            ],
            self.Columns.NUMBER_OF_STATOBJ: [
                ".EM_DATA.EmApEnvModelPort.numberOfStaticObjects_u8",
                ".SI_DATA.m_environmentModelPort.numberOfStaticObjects_u8",
            ],
            self.Columns.NUMBER_OF_VALID_PB: [
                ".EM_DATA.EmApParkingBoxPort.numValidParkingBoxes_nu",
                ".SI_DATA.m_parkingBoxesPort.numValidParkingBoxes_nu",
            ],
            self.Columns.NUMBER_OF_VALID_POSES: [
                ".TRJPLA_DATA.TrjPlaTargetPosesPort.numValidPoses",
                ".MF_TRJPLA_DATA.targetPoses.numValidPoses",
            ],
            self.Columns.SELECTED_PB_ID: [
                ".EM_DATA.EmSlotCtrlPort.selectedParkingBoxId_nu",
                ".MF_PARKSM_CORE_DATA.slotCtrlPort.selectedParkingBoxId_nu",
            ],
            self.Columns.SCREEN_NU: [
                ".EM_DATA.EmHeadUnitVisualizationPort.screen_nu",
                "MTA_ADC5.APPDEMO_HMIH_DATA.headUnitVisualizationPort.screen_nu",
            ],
            self.Columns.sg_time: [
                ".USP_DATA.SpuOdoEstimationOutputPort.sSigHeader.uiTimeStamp",
                "MTA_ADC5.APPDEMO_HMIH_DATA.headUnitVisualizationPort.sSigHeader.uiTimeStamp",
            ],
            self.Columns.VELOCITY: [
                "Reference_RT3000_Ethernet.Hunter.VelocityVehicle.LongitudinalVelocity_kph",
                ".Conti_Veh_CAN.VehVelocity.VehVelocityExt",
                "AP_Conti_CAN.AP_Conti_CAN_1_0_10.VehVelocity.VehVelocityExt",
            ],
            self.Columns.HMI_PS_RIGHT_0: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.right.scanned_nu[0]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.right.scanned_nu[0]",
            ],
            self.Columns.HMI_PS_RIGHT_1: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.right.scanned_nu[1]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.right.scanned_nu[1]",
            ],
            self.Columns.HMI_PS_RIGHT_2: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.right.scanned_nu[2]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.right.scanned_nu[2]",
            ],
            self.Columns.HMI_PS_RIGHT_3: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.right.scanned_nu[3]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.right.scanned_nu[3]",
            ],
            self.Columns.HMI_PS_LEFT_0: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.left.scanned_nu[0]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.left.scanned_nu[0]",
            ],
            self.Columns.HMI_PS_LEFT_1: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.left.scanned_nu[1]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.left.scanned_nu[1]",
            ],
            self.Columns.HMI_PS_LEFT_2: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.left.scanned_nu[2]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.left.scanned_nu[2]",
            ],
            self.Columns.HMI_PS_LEFT_3: [
                ".EM_DATA.EmHMIGeneralInputPort.parkingSpaces.left.scanned_nu[3]",
                "MTA_ADC5.APPDEMO_HMIH_DATA.hmiInputPort.parkingSpaces.left.scanned_nu[3]",
            ],
            # self.Columns.PATH_FOUND: [".TRJPLA_DATA.TrjPlaTargetPosesPort.anyPathFound",".MF_TRJPLA_DATA.targetPoses.anyPathFound"],
            # self.Columns.FAIL_REASON: [".TRJPLA_DATA.TrjPlaTargetPosesPort.failReason",".MF_TRJPLA_DATA.targetPoses.failReason"],
            # self.Columns.SOFTWARE_MAJOR: ".ApplicationReleaseInfo.softwareVersion.major",
            # self.Columns.SOFTWARE_MINOR: ".ApplicationReleaseInfo.softwareVersion.minor",
            # self.Columns.SOFTWARE_PATCH: ".ApplicationReleaseInfo.softwareVersion.patch",
        }


signals_obj = Signals()
verdict_obj = StoreStepResults()


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that vehicle velocity[km/h] has values greater than 0 until a slot is selected by the driver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class VEDODO_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------
    Verify that vehicle velocity[km/h] has values greater than 0 until a slot is selected by the driver.

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_1 = fc.INPUT_MISSING

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            # Converting microseconds to seconds
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] / constants.GeneralConstants.US_IN_S
            # Converting epoch time to seconds passed
            df[Signals.Columns.TIMESTAMP] = df[Signals.Columns.TIMESTAMP] - df[Signals.Columns.TIMESTAMP].iat[0]
            global time
            time = df[Signals.Columns.TIMESTAMP]

            velocity = df[Signals.Columns.VELOCITY]
            pb_id = df[Signals.Columns.SELECTED_PB_ID]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.VELOCITY} is FAILED because has only values"
                f" <= {0} during the scanning period of measurement.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SELECTED_PB_ID]):
                if val == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False]
                for idx in range(t2, len(df[Signals.Columns.SELECTED_PB_ID])):
                    if df[Signals.Columns.SELECTED_PB_ID].iloc[idx] == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                        if df[Signals.Columns.VELOCITY].iloc[idx] > 0:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.VELOCITY} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[0] = True
                    else:
                        break

                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_1 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_1 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = f"Trigger not found!(ParkingBoxID=={constants.RootCauseAnalysis.NO_SLOT_SELECT})"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_1 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Vehicle velocity [kph]"] = evaluation1
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            # to add time in seconds
            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=time, y=velocity, mode="lines", name=Signals.Columns.VELOCITY))
            self.fig.add_trace(
                go.Scatter(x=time, y=pb_id, mode="lines", name=Signals.Columns.SELECTED_PB_ID, visible="legendonly")
            )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")  # to modify to appear only then failed
            plots.append(self.fig)
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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=2,
    name="US",
    description="Verify that number of points and echos detected by ultrasonic sensor has values greater than 0 until a slot is selected by the driver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class US_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            script_directory = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(script_directory, "UseCases.json")
            usecases_file = open(json_path)
            usecases_data = json.load(usecases_file)
            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )

            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_2 = fc.NOT_ASSESSED

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}
            usecase_const = True
            # try to find if measurement name contain use case
            for _, data in enumerate(usecases_data):
                if self.result.details["file_name"].find(data["Use_Case"]) != -1:
                    if data["USS"].isalnum() is False:
                        usecase_const = False

            usecases_file.close()

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            num_of_point = df[Signals.Columns.NUMBER_OF_POINTS]
            num_of_echos = df[Signals.Columns.NUMBER_OF_ECHOS]
            pb_id = df[Signals.Columns.SELECTED_PB_ID]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_POINTS} is FAILED because the values"
                f" are <= 0 during all scanning period.".split()
            )
            evaluation2 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_ECHOS} is FAILED because the values"
                f" are <= 0 during all scanning period.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SELECTED_PB_ID]):
                if val == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False] * 2

                for idx in range(t2, len(df[Signals.Columns.SELECTED_PB_ID])):
                    if df[Signals.Columns.SELECTED_PB_ID].iloc[idx] == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                        if df[Signals.Columns.NUMBER_OF_POINTS].iloc[idx] > 0:  # to eliminate eval cond from if cond
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_POINTS} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[0] = True

                        if df[Signals.Columns.NUMBER_OF_ECHOS].iloc[idx] > 0:

                            evaluation2 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_ECHOS} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[1] = True
                    else:
                        break
                    if usecase_const:
                        if all(eval_cond):
                            self.result.measured_result = TRUE
                            verdict_obj.step_2 = fc.PASS
                            self.result.details["root_cause_text"] = "passed"
                        else:
                            self.result.measured_result = FALSE
                            verdict_obj.step_2 = fc.FAIL
                            self.result.details["root_cause_text"] = "failed"
                    else:
                        evaluation1 = evaluation2 = "USS component is not evaluated for this measurement"
            else:
                evaluation1 = evaluation2 = (
                    f"Trigger not found! (ParkingBoxID=={constants.RootCauseAnalysis.NO_SLOT_SELECT})"
                )
                self.result.measured_result = FALSE
                verdict_obj.step_2 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of points detected by ultrasonic sensors"] = evaluation1
            signal_summary["Number of echoes detected by ultrasonic sensors"] = evaluation2
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=time, y=num_of_point, mode="lines", name=Signals.Columns.NUMBER_OF_POINTS))
            self.fig.add_trace(go.Scatter(x=time, y=num_of_echos, mode="lines", name=Signals.Columns.NUMBER_OF_ECHOS))
            self.fig.add_trace(
                go.Scatter(x=time, y=pb_id, mode="lines", name=Signals.Columns.SELECTED_PB_ID, visible="legendonly")
            )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(self.fig)
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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=3,
    name="PMSD",
    description="Verify that number of parking lines detected by cameras has values greater than 0 until a slot is selected by the driver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class PMSD_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            script_directory = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(script_directory, "UseCases.json")
            usecases_file = open(json_path)
            usecases_data = json.load(usecases_file)

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_3 = fc.NOT_ASSESSED

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}
            usecase_const = True
            # try to find if measurement name contain use case
            for _, data in enumerate(usecases_data):
                if self.result.details["file_name"].find(data["Use_Case"]) != -1:
                    if data["PMSD"].isalnum() is False:
                        usecase_const = False

            usecases_file.close()

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            lines_fc = df[Signals.Columns.NUMBER_OF_LINES_FC]
            lines_lsc = df[Signals.Columns.NUMBER_OF_LINES_LSC]
            lines_rc = df[Signals.Columns.NUMBER_OF_LINES_RC]
            lines_rsc = df[Signals.Columns.NUMBER_OF_LINES_RSC]
            pb_id = df[Signals.Columns.SELECTED_PB_ID]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_FC} is FAILED because the values"
                f" are <= 0 during all scanning period.".split()
            )

            evaluation2 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_LSC} is FAILED because the values"
                f" are <= 0 during all scanning period.".split()
            )

            evaluation3 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_RC} is FAILED because the values"
                f" are <= 0 during all scanning period.".split()
            )

            evaluation4 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_RSC} is FAILED because the values"
                f" are <= 0 during all scanning period.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SELECTED_PB_ID]):
                if val == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False] * 4

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SELECTED_PB_ID].iloc[idx] == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                        if df[Signals.Columns.NUMBER_OF_LINES_FC].iloc[idx] > 0:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_FC} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[0] = True

                        if df[Signals.Columns.NUMBER_OF_LINES_LSC].iloc[idx] > 0:
                            evaluation2 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_LSC} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[1] = True
                        if df[Signals.Columns.NUMBER_OF_LINES_RC].iloc[idx] > 0:
                            evaluation3 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_RC} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[2] = True

                        if df[Signals.Columns.NUMBER_OF_LINES_RSC].iloc[idx] > 0:
                            evaluation4 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_LINES_RSC} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[3] = True
                    if usecase_const:
                        if all(eval_cond):
                            self.result.measured_result = TRUE
                            verdict_obj.step_3 = fc.PASS
                            self.result.details["root_cause_text"] = "passed"
                        else:
                            self.result.measured_result = FALSE
                            verdict_obj.step_3 = fc.FAIL
                            self.result.details["root_cause_text"] = "failed"
                    else:
                        evaluation1 = evaluation2 = evaluation3 = evaluation4 = (
                            "PMSD component is not evaluated for this measurement"
                        )
            else:
                evaluation1 = evaluation2 = evaluation3 = evaluation4 = (
                    f"Trigger not found! (ParkingBoxID=={constants.RootCauseAnalysis.NO_SLOT_SELECT})"
                )
                self.result.measured_result = DATA_NOK
                verdict_obj.step_3 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of parking lines detected by front camera"] = evaluation1
            signal_summary["Number of parking lines detected by left camera"] = evaluation2
            signal_summary["Number of parking lines detected by rear camera"] = evaluation3
            signal_summary["Number of parking lines detected by right camera"] = evaluation4
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=time, y=lines_fc, mode="lines", name=Signals.Columns.NUMBER_OF_LINES_FC))
            self.fig.add_trace(go.Scatter(x=time, y=lines_lsc, mode="lines", name=Signals.Columns.NUMBER_OF_LINES_LSC))
            self.fig.add_trace(go.Scatter(x=time, y=lines_rc, mode="lines", name=Signals.Columns.NUMBER_OF_LINES_RC))
            self.fig.add_trace(go.Scatter(x=time, y=lines_rsc, mode="lines", name=Signals.Columns.NUMBER_OF_LINES_RSC))
            self.fig.add_trace(
                go.Scatter(x=time, y=pb_id, mode="lines", name=Signals.Columns.SELECTED_PB_ID, visible="legendonly")
            )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(self.fig)
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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=4,
    name="CEM",
    description="Verify that number of parking slot delimiters and of fusion objects has values greater than 0 until a slot is selected by the driver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class CEM_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_4 = fc.NOT_ASSESSED

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            num_delim = df[Signals.Columns.NUMBER_OF_DELIMITERS]
            num_obj = df[Signals.Columns.NUMBER_OF_OBJECTS]
            pb_id = df[Signals.Columns.SELECTED_PB_ID]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_DELIMITERS} is FAILED because the values"
                f" are <= 0 during all scanning period.".split()
            )

            evaluation2 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_OBJECTS} is FAILED because the values"
                f" are <= 0 during all scanning period.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SELECTED_PB_ID]):
                if val == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False] * 2

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SELECTED_PB_ID].iloc[idx] == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                        if num_delim.iloc[idx] > 0:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_DELIMITERS} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[0] = True

                        if num_obj.iloc[idx] > 0:
                            evaluation2 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_OBJECTS} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[1] = True

                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_4 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_4 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = evaluation2 = (
                    f"Trigger not found! (ParkingBoxID=={constants.RootCauseAnalysis.NO_SLOT_SELECT})"
                )
                self.result.measured_result = DATA_NOK
                verdict_obj.step_4 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of parking slot delimeters"] = evaluation1
            signal_summary["Number of fusion objects"] = evaluation2
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.fig = go.Figure()
            self.fig.add_trace(go.Scatter(x=time, y=num_delim, mode="lines", name=Signals.Columns.NUMBER_OF_DELIMITERS))
            self.fig.add_trace(go.Scatter(x=time, y=num_obj, mode="lines", name=Signals.Columns.NUMBER_OF_OBJECTS))
            self.fig.add_trace(
                go.Scatter(x=time, y=pb_id, mode="lines", name=Signals.Columns.SELECTED_PB_ID, visible="legendonly")
            )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(self.fig)
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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=5,
    name="SI",
    description="Verify that number of parking markings, of static objects and of valid parking boxes has values greater than 0 until a slot is selected by the driver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class SI_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:
            script_directory = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(script_directory, "UseCases.json")
            usecases_file = open(json_path)
            usecases_data = json.load(usecases_file)

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_5 = fc.NOT_ASSESSED

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}
            usecase_const_uss = True
            usecase_const_pmsd = True

            # try to find if measurement name contain use case
            for _, data in enumerate(usecases_data):
                if self.result.details["file_name"].find(data["Use_Case"]) != -1:
                    if not data["USS"].isalnum():
                        usecase_const_uss = False
                    if not data["PMSD"].isalnum():
                        usecase_const_pmsd = False

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index
            eval_cond = [False] * 3
            num_of_parkmark = df[Signals.Columns.NUMBER_OF_PARKMARK]
            num_of_statobj = df[Signals.Columns.NUMBER_OF_STATOBJ]
            num_of_validpb = df[Signals.Columns.NUMBER_OF_VALID_PB]
            pb_id = df[Signals.Columns.SELECTED_PB_ID]

            if usecase_const_pmsd:
                evaluation1 = " ".join(
                    f"The evaluation of {Signals.Columns.NUMBER_OF_PARKMARK} is FAILED because the values"
                    f" are <= 0 during all scanning period.".split()
                )
            else:
                evaluation1 = "PMSD component is not evaluated for this measurement"
                eval_cond[0] = [True]
            if usecase_const_uss:
                evaluation2 = " ".join(
                    f"The evaluation of {Signals.Columns.NUMBER_OF_STATOBJ} is FAILED because the values"
                    f" are <= 0 during all scanning period.".split()
                )
            else:
                evaluation2 = "USS component is not evaluated for this measurement"
                eval_cond[1] = [True]

            evaluation3 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_VALID_PB} is FAILED because the values"
                f" are <= 0 during all scanning period.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SELECTED_PB_ID]):
                if val == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                    t2 = idx
                    break
            if t2 is not None:

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SELECTED_PB_ID].iloc[idx] == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                        if usecase_const_pmsd:
                            if df[Signals.Columns.NUMBER_OF_PARKMARK].iloc[idx] > 0:
                                evaluation1 = " ".join(
                                    f"The evaluation of {Signals.Columns.NUMBER_OF_PARKMARK} is PASSED with values > than"
                                    f" {0} .".split()
                                )
                                eval_cond[0] = True

                        if usecase_const_uss:
                            if df[Signals.Columns.NUMBER_OF_STATOBJ].iloc[idx] > 0:
                                evaluation2 = " ".join(
                                    f"The evaluation of {Signals.Columns.NUMBER_OF_STATOBJ} is PASSED with values > than"
                                    f" {0} .".split()
                                )
                                eval_cond[1] = True

                        if df[Signals.Columns.NUMBER_OF_VALID_PB].iloc[idx] > 0:
                            evaluation3 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_VALID_PB} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[2] = True
                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_5 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_5 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = evaluation2 = evaluation3 = (
                    f"Trigger not found! (ParkingBoxID=={constants.RootCauseAnalysis.NO_SLOT_SELECT})"
                )
                self.result.measured_result = DATA_NOK
                verdict_obj.step_5 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of parking markings"] = evaluation1
            signal_summary["Number of static objects"] = evaluation2
            signal_summary["Number of valid parking boxes"] = evaluation3
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(x=time, y=num_of_parkmark, mode="lines", name=Signals.Columns.NUMBER_OF_PARKMARK)
            )
            self.fig.add_trace(
                go.Scatter(x=time, y=num_of_statobj, mode="lines", name=Signals.Columns.NUMBER_OF_STATOBJ)
            )
            self.fig.add_trace(
                go.Scatter(x=time, y=num_of_validpb, mode="lines", name=Signals.Columns.NUMBER_OF_VALID_PB)
            )
            self.fig.add_trace(
                go.Scatter(x=time, y=pb_id, mode="lines", name=Signals.Columns.SELECTED_PB_ID, visible="legendonly")
            )
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(self.fig)
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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=6,
    name="TRJPLA",
    description="Verify that number of valid target poses has values greater than 0 until a slot is selected by the driver.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class TRJPLA_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_6 = fc.NOT_ASSESSED

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            num_validpos = df[Signals.Columns.NUMBER_OF_VALID_POSES]
            pb_id = df[Signals.Columns.SELECTED_PB_ID]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.NUMBER_OF_VALID_POSES} is FAILED because the values"
                f" are <= 0 during all of scanning period.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SELECTED_PB_ID]):
                if val == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False]

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if df[Signals.Columns.SELECTED_PB_ID].iloc[idx] == constants.RootCauseAnalysis.NO_SLOT_SELECT:
                        if df[Signals.Columns.NUMBER_OF_VALID_POSES].iloc[idx] > 0:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.NUMBER_OF_VALID_POSES} is PASSED with values > than"
                                f" {0} .".split()
                            )
                            eval_cond[0] = True

                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_6 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_6 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = f"Trigger not found! (ParkingBoxID=={constants.RootCauseAnalysis.NO_SLOT_SELECT})"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_6 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Number of valid target poses"] = evaluation1
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(x=time, y=num_validpos, mode="lines", name=Signals.Columns.NUMBER_OF_VALID_POSES)
            )
            self.fig.add_trace(
                go.Scatter(x=time, y=pb_id, mode="lines", name=Signals.Columns.SELECTED_PB_ID, visible="legendonly")
            )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(self.fig)
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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=7,
    name="TAPOSD",
    description="Verify that parking box ID selected by the driver has a value different of 255(No slot is selected by the driver) in scanning phase.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class TAPOSD_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_7 = fc.NOT_ASSESSED

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            pb_id = df[Signals.Columns.SELECTED_PB_ID]
            screen_nu = df[Signals.Columns.SCREEN_NU]

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.SELECTED_PB_ID} is FAILED because the values"
                f" are == {constants.RootCauseAnalysis.NO_SLOT_SELECT} during all period of scanning phase.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
                if val == constants.RootCauseAnalysis.SCANNING_ACTIVE:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False]

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if (
                        screen_nu.iloc[idx] == constants.RootCauseAnalysis.PARKING_SPACE_SELECTION
                        or screen_nu.iloc[idx] == constants.RootCauseAnalysis.SCANNING_ACTIVE
                    ):  # to discus with David
                        if df[Signals.Columns.SELECTED_PB_ID].iloc[idx] != constants.RootCauseAnalysis.NO_SLOT_SELECT:
                            evaluation1 = " ".join(
                                f"The evaluation of {Signals.Columns.SELECTED_PB_ID} is PASSED with values different than"
                                f" {constants.RootCauseAnalysis.NO_SLOT_SELECT} .".split()
                            )
                            eval_cond[0] = True

                    if all(eval_cond):
                        self.result.measured_result = TRUE
                        verdict_obj.step_7 = fc.PASS
                        self.result.details["root_cause_text"] = "passed"
                    else:
                        self.result.measured_result = FALSE
                        verdict_obj.step_7 = fc.FAIL
                        self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = "Trigger not found!(SCREEN_NU does not have scanning phase)"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_7 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Parking box ID selected by the driver"] = evaluation1
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(x=time, y=screen_nu, mode="lines", name=Signals.Columns.SCREEN_NU, text=df["status"])
            )
            self.fig.add_trace(go.Scatter(x=time, y=pb_id, mode="lines", name=Signals.Columns.SELECTED_PB_ID))

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", "SCANNING_ACTIVE"
            )
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
            plot_titles.append("")
            plots.append(self.fig)
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

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@teststep_definition(
    step_number=8,
    name="HMI",
    description="Verify that in the signal SCREEN.NU from HMI is present a visibile transition between 1(SCANNING_ACTIVE) and 2(PARKING_SPACE_SELECTION).",
    expected_result=BooleanResult(TRUE),
)
@register_signals(EXAMPLE, Signals)
class HMI_STEP(TestStep):
    """testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    # custom_report = CustomTeststepReport
    custom_report = fh.MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")
        try:

            self.result.details.update(
                {
                    "Plots": [],
                    "software_version_file": "",
                    "Km_driven": 0,
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            self.result.details["root_cause_text"] = "not assessed"
            self.result.measured_result = DATA_NOK
            verdict_obj.step_8 = fc.NOT_ASSESSED

            plot_titles, plots, remarks = fh.rep([], 3)
            t2 = None
            signal_summary = {}

            df = self.readers[EXAMPLE]  # for rrec
            df[Signals.Columns.TIMESTAMP] = df.index

            # parkspace_right0 = []
            # parkspace_right1 = []
            # parkspace_right2 = []
            # parkspace_right3 = []
            # parkspace_left0 = []
            # parkspace_left1 = []
            # parkspace_left2 = []
            # parkspace_left3 = []

            screen_nu = df[Signals.Columns.SCREEN_NU]
            # for idx in range(0, len(df[Signals.Columns.SCREEN_NU])):
            #     parkspace_right0.append(df[Signals.Columns.HMI_PS_RIGHT_0].iloc[idx][0])
            #     parkspace_right1.append(df[Signals.Columns.HMI_PS_RIGHT_0].iloc[idx][1])
            #     parkspace_right2.append(df[Signals.Columns.HMI_PS_RIGHT_0].iloc[idx][2])
            #     parkspace_right3.append(df[Signals.Columns.HMI_PS_RIGHT_0].iloc[idx][3])
            #     parkspace_left0.append(df[Signals.Columns.HMI_PS_LEFT_0].iloc[idx][0])
            #     parkspace_left1.append(df[Signals.Columns.HMI_PS_LEFT_0].iloc[idx][1])
            #     parkspace_left2.append(df[Signals.Columns.HMI_PS_LEFT_0].iloc[idx][2])
            #     parkspace_left3.append(df[Signals.Columns.HMI_PS_LEFT_0].iloc[idx][3])

            evaluation1 = " ".join(
                f"The evaluation of {Signals.Columns.SCREEN_NU} is FAILED because"
                f"a visible transition between screen_nu ==1 and screen_nu ==2 does not exist.".split()
            )

            for idx, val in enumerate(df[Signals.Columns.SCREEN_NU]):
                if val != 0:
                    t2 = idx
                    break
            if t2 is not None:
                eval_cond = [False]

                for idx in range(t2, len(df[Signals.Columns.SCREEN_NU])):
                    if (
                        df[Signals.Columns.SCREEN_NU].iloc[idx - 1] == 1
                        and df[Signals.Columns.SCREEN_NU].iloc[idx] == 2
                    ):
                        evaluation1 = " ".join(
                            f"The evaluation of {Signals.Columns.SCREEN_NU} is PASSED with visible transition between values == 1 ."
                            f" and values == 2".split()
                        )
                        eval_cond[0] = True

                if all(eval_cond):
                    self.result.measured_result = TRUE
                    verdict_obj.step_8 = fc.PASS
                    self.result.details["root_cause_text"] = "passed"
                else:
                    self.result.measured_result = FALSE
                    verdict_obj.step_8 = fc.FAIL
                    self.result.details["root_cause_text"] = "failed"
            else:
                evaluation1 = "Trigger not found!(SCREEN_NU does not have scanning phase)"
                self.result.measured_result = DATA_NOK
                verdict_obj.step_8 = fc.NOT_ASSESSED
                self.result.details["root_cause_text"] = "not assessed"

            signal_summary["Slot offered on HMI"] = evaluation1
            self.sig_sum = convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")
            df["status"] = screen_nu.apply(lambda x: fh.get_status_label(x, constants.RootCauseAnalysis))

            self.fig = go.Figure()
            self.fig.add_trace(
                go.Scatter(x=time, y=screen_nu, mode="lines", name=Signals.Columns.SCREEN_NU, text=df["status"])
            )
            # self.fig.add_trace(
            #     go.Scatter(
            #         x=time, y=parkspace_right0, mode="lines", name=Signals.Columns.HMI_PS_RIGHT_0, visible="legendonly"
            #     )
            # )
            # self.fig.add_trace(
            #     go.Scatter(
            #         x=time, y=parkspace_right1, mode="lines", name=Signals.Columns.HMI_PS_RIGHT_1, visible="legendonly"
            #     )
            # )
            # self.fig.add_trace(
            #     go.Scatter(
            #         x=time, y=parkspace_right2, mode="lines", name=Signals.Columns.HMI_PS_RIGHT_2, visible="legendonly"
            #     )
            # )
            # self.fig.add_trace(
            #     go.Scatter(
            #         x=time, y=parkspace_right3, mode="lines", name=Signals.Columns.HMI_PS_RIGHT_3, visible="legendonly"
            #     )
            # )
            # self.fig.add_trace(
            #     go.Scatter(
            #         x=time, y=parkspace_left0, mode="lines", name=Signals.Columns.HMI_PS_LEFT_0, visible="legendonly"
            #     )
            # )
            # self.fig.add_trace(
            #     go.Scatter(
            #         x=time, y=parkspace_left1, mode="lines", name=Signals.Columns.HMI_PS_LEFT_1, visible="legendonly"
            #     )
            # )
            # self.fig.add_trace(
            #     go.Scatter(
            #         x=time, y=parkspace_left2, mode="lines", name=Signals.Columns.HMI_PS_LEFT_2, visible="legendonly"
            #     )
            # )
            # self.fig.add_trace(
            #     go.Scatter(
            #         x=time, y=parkspace_left3, mode="lines", name=Signals.Columns.HMI_PS_LEFT_3, visible="legendonly"
            #     )
            # )

            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
            fh.highlight_segments(
                self.fig, screen_nu, constants.RootCauseAnalysis.SCANNING_ACTIVE, time, "LightSalmon", "SCANNING_ACTIVE"
            )
            self.fig.update_layout(constants.PlotlyTemplate.lgt_tmplt, showlegend=True)
            plot_titles.append("")
            plots.append(self.fig)
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

            verdict, color = verdict_obj.check_result()

            additional_results_dict = {
                "Verdict": {"value": verdict.title(), "color": color},
            }
            self.result.details["Additional_results"] = additional_results_dict

        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("req-001")
@testcase_definition(
    name="Slot offering Root Cause Analysis", description="Verify the output checks of components for slot offering."
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SlotOfferRootCause(TestCase):
    # custom_report = CustomTestcaseReport
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            # PreAnalysisSTEP,
            VEDODO_STEP,
            US_STEP,
            PMSD_STEP,
            CEM_STEP,
            SI_STEP,
            TRJPLA_STEP,
            TAPOSD_STEP,
            HMI_STEP,
        ]


def convert_dict_to_pandas(signal_summary: dict, table_remark="", table_title=""):
    """Converts a dictionary to a Pandas DataFrame and creates an HTML table."""
    evaluation_summary = pd.DataFrame(
        {
            "Evaluation": {key: key for key, val in signal_summary.items()},
            "Results": {key: val for key, val in signal_summary.items()},
        }
    )
    return fh.build_html_table(
        evaluation_summary,
        table_remark,
        table_title,
    )
