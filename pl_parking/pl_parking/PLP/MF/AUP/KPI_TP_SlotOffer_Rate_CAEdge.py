"""
This module defines test steps and a test case for verifying the true positive slot offer rate in a parking scenario.
Classes:
    NextToParkingBoxCAEdge: Handles the test step for checking the overlap percentage when the car mirrors reach the front of the designated parking area.
    AfterParkingBoxCAEdge: Handles the test step for checking the overlap percentage as the rear of the car approaches the point where it has completely passed the parking slot.
    SelectedOfferedSlotCAEdge: Defines the test case for verifying the true positive slot offer rate.
Constants:
    EXAMPLE: The example signal name for the test.
    EXPECTED_RESULT_NEXT_TO_PB: The expected result for the "Next to parking box" test step.
    EXPECTED_RESULT_AFTER_PB: The expected result for the "Fully passed the parking box" test step.
Decorators:
    @teststep_definition: Defines a test step with metadata such as step number, name, description, and expected result.
    @register_signals: Registers the signals to be used in the test step.
    @verifies: Links the test case to a requirement ID.
    @testcase_definition: Defines a test case with metadata such as name, doors URL, and description.
    @register_inputs: Registers the input paths for the test case.
Functions:
    process: Processes the test result and sets the measured result.
"""

import os
import sys

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

from tsf.core.common import PathSpecification
from tsf.core.testcase import (
    PreProcessor,
    TestCase,
    register_inputs,
    register_pre_processor,
    register_side_load,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.sideload import JsonSideLoad

import pl_parking.common_ft_helper as fh

# from pl_parking.PLP.MF.PARKSM.ft_parksm import StatisticsExample
from pl_parking.common_ft_helper import MfCustomTestcaseReport
from pl_parking.PLP.MF.AUP.kpi_TP_SlotOffer_Rate import AfterPBStep, NextToPBStep, Signals

__author__ = "BA ADAS ENP SIMU KPI"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

EXPECTED_RESULT_NEXT_TO_PB = "= 100 %"
EXPECTED_RESULT_AFTER_PB = "= 100 %"
ALIAS_JSON = "KPI_TP_SlotOffer_Rate_CAEdge_JSON"
ALIAS = "KPI_TP_SlotOffer_Rate_CAEdge"


class PreprocessorCAEdge(PreProcessor):
    """Preprocessor for the ParkEnd test step."""

    def pre_process(self):
        """
        Preprocesses the data before further processing.

        Returns:
        - df: pd.DataFrame, the preprocessed data.
        """

        def get_time_obj_string(file_data):
            # Extract VehicleLocal from file_data
            vehicle_local_string = "VehicleLocal" if "VehicleLocal" in file_data else "VehicleLocalSlots"
            vehicle_local_coordinates = file_data.get("VehicleLocal") or file_data.get("VehicleLocalSlots")
            if not vehicle_local_coordinates:
                raise ValueError("VehicleLocal not found in JSON file")

            # Extract timedObjs from the first element of VehicleLocal
            timed_objs = vehicle_local_coordinates[0].get("timedObjs")
            if not timed_objs:
                raise ValueError("timedObjs not found in VehicleLocal")

            # Look for the key that ends with ".uiTimeStamp" in the first element of timedObjs
            for key in timed_objs[0].keys():
                if key.endswith(".uiTimeStamp"):
                    return key, vehicle_local_string

            # If no key ending with '.uiTimeStamp' is found, raise an error
            raise ValueError("No key ending with '.uiTimeStamp' found in timedObjs")

        time_obj_string_timestamp = None
        vehicle_local_string = None
        try:
            if ALIAS_JSON in self.side_load:
                file_data = self.side_load[ALIAS_JSON]
                time_obj_string_timestamp, vehicle_local_string = get_time_obj_string(file_data)
            else:
                raise FileNotFoundError("Alias JSON data not found in side load.")
        except Exception as exc:
            raise FileNotFoundError("No JSON file found matching the identifier.") from exc

        return file_data, time_obj_string_timestamp, vehicle_local_string


@teststep_definition(
    step_number=1,
    name="Next to parking box",
    description="The overlap percentage should be calculated when the mirrors of the car are reaching the front of \
                    the designated parking area (0.5 meters beyond the initial line of the targeted slot).",
    expected_result=EXPECTED_RESULT_NEXT_TO_PB,
)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True
        # folder=r"D:\SLOT_OFFER_RRECS_FOR_MLC60\2024.11.18_at_15.09.11_radar-mi_9025", extension=".json"
    ),  # CAEdge path
)
@register_signals(ALIAS, Signals)
@register_pre_processor(alias="AUP_slot_offer_CAEdge", pre_processor=PreprocessorCAEdge)
class NextToParkingBoxCAEdge(NextToPBStep):
    """Class to handle the test step for checking the overlap percentage when
    the car mirrors reach the front of the designated parking area.
    """

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Fully passed the parking box",
    description="The overlap percentage should be calculated as the rear of the car approaches the point where it has \
                    completely passed the parking slot.",
    expected_result=EXPECTED_RESULT_AFTER_PB,
)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True
        # folder=r"D:\SLOT_OFFER_RRECS_FOR_MLC60\2024.11.18_at_15.09.11_radar-mi_9025", extension=".json"
    ),  # CAEdge path
)
@register_signals(ALIAS, Signals)
@register_pre_processor(alias="AUP_slot_offer_CAEdge", pre_processor=PreprocessorCAEdge)
class AfterParkingBoxCAEdge(AfterPBStep):
    """Class to handle the test step for checking the overlap percentage as the rear of the car
    approaches the point where it has completely passed the parking slot.
    """

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("966639")
@testcase_definition(
    name="AUP Slot Offer TestCase for CAEdge running",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_PfAN_8lcEe2iKqc0KPO99Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_lWHOEPvsEeqIqKySVwTVNQ%2Fcomponents%2F_u4eQYMlKEe2iKqc0KPO99Q&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
    description="The true positive slot offer rate considers the total number of times a particular scanned slot \
        is offered (true positive) by the AP function.\
        The Pass rate is calculated for each test step as follows: \
        TPR = (Number of measurements where a slot was offered with a \
            overlap > 80%)/(Number of total measurements)",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SelectedOfferedSlotCAEdge(TestCase):
    """TP SlotOffer test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            NextToParkingBoxCAEdge,
            AfterParkingBoxCAEdge,
        ]
