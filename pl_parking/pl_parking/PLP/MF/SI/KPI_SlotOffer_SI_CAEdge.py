"""
This module defines test steps and a test case for verifying the slot offer rates in a parking scenario for CAEdge.
Classes:
    Preprocessor: Preprocesses the data before further processing.
    TPTestStepCAEdge: Handles the test step for the true positive rate.
    FPTestStepCAEdge: Handles the test step for the false positive rate.
    FNTestStepCAEdge: Handles the test step for the false negative rate.
    SISlotOfferRateCAEdge: Defines the test case for verifying the slot offer rates.
Decorators:
    @teststep_definition: Defines a test step with metadata such as step number, name, description, and expected result.
    @register_side_load: Registers the side load to be used in the test step.
    @register_signals: Registers the signals to be used in the test step.
    @register_pre_processor: Registers the pre-processor to be used in the test step.
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

from pl_parking.common_ft_helper import MfCustomTestcaseReport
from pl_parking.PLP.MF.constants import SlotOffer
from pl_parking.PLP.MF.SI.KPI_SlotOffer_SI import FNTestStep, FPTestStep, Signals, TPTestStep

__author__ = "BA ADAS ENP SIMU KPI"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

EXAMPLE = "SLOT_OFFER_SI_CAEdge"
ALIAS_JSON = "KPI_SlotOffer_SI_CAEdge_JSON"
ALIAS = "KPI_SlotOffer_SI_CAEdge"


class Preprocessor(PreProcessor):
    """Preprocessor for the ParkEnd test step."""

    def pre_process(self):
        """
        Preprocesses the data before further processing.

        Returns:
        - df: pd.DataFrame, the preprocessed data.
        """

        def get_time_obj_string(file_data):
            # Extract VehicleLocal from file_data
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
                    return key

            # If no key ending with '.uiTimeStamp' is found, raise an error
            raise ValueError("No key ending with '.uiTimeStamp' found in timedObjs")

        time_obj_string_timestamp = None

        try:
            if ALIAS_JSON in self.side_load:
                file_data = self.side_load[ALIAS_JSON]
                time_obj_string_timestamp = get_time_obj_string(file_data)
            else:
                raise FileNotFoundError("Alias JSON data not found in side load.")
        except Exception as exc:
            raise FileNotFoundError("No JSON file found matching the identifier.") from exc

        return file_data, time_obj_string_timestamp


@teststep_definition(
    step_number=1,
    name="True Positive Rate",
    description=f"The True Positive Rate should be greater than {SlotOffer.Thresholds.THRESHOLD_TPR}%.",
    expected_result=f"> {SlotOffer.Thresholds.THRESHOLD_TPR} %",
)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True
    ),  # CAEdge path
)
@register_signals(ALIAS, Signals)
@register_pre_processor(alias="SI_slot_offer_CAEdge", pre_processor=Preprocessor)
class TPTestStepCAEdge(TPTestStep):
    """Class to handle the test step for the true positive rate."""

    def process(self, **kwargs):
        """Process the test result."""
        super().process()


@teststep_definition(
    step_number=2,
    name="False Positive Rate",
    description=f"The False Positive Rate should be less than {SlotOffer.Thresholds.THRESHOLD_FPR}%.",
    expected_result=f"< {SlotOffer.Thresholds.THRESHOLD_FPR} %",
)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True
    ),  # CAEdge path
)
@register_signals(ALIAS, Signals)
@register_pre_processor(alias="SI_slot_offer_CAEdge", pre_processor=Preprocessor)
class FPTestStepCAEdge(FPTestStep):
    """Class to handle the test step for the false positive rate."""

    def process(self, **kwargs):
        """Process the test result."""
        super().process()


@teststep_definition(
    step_number=3,
    name="False Negative Rate",
    description=f"The False Negative Rate should be less than {SlotOffer.Thresholds.THRESHOLD_FNR}%.",
    expected_result=f"< {SlotOffer.Thresholds.THRESHOLD_FNR} %",
)
@register_side_load(
    alias=ALIAS_JSON,
    side_load=JsonSideLoad,
    path_spec=PathSpecification(
        folder=r"s3://par230-prod-data-lake-sim/gt_labels/", extension=".json", s3=True
    ),  # CAEdge path
)
@register_signals(ALIAS, Signals)
@register_pre_processor(alias="SI_slot_offer_CAEdge", pre_processor=Preprocessor)
class FNTestStepCAEdge(FNTestStep):
    """Class to handle the test step for the false positive rate."""

    def process(self, **kwargs):
        """Process the test result."""
        super().process()


@verifies("1780700")
@testcase_definition(
    name="SI Slot Offer TestCase for CAEdge running",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FMD_K4BUUCvLEe6mrdm2_agUYg&vvc.configuration=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fcm%2Fstream%2F_G3kr8DgnEe6mrdm2_agUYg&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&artifactInModule=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_8BbkUJs4Ee6Zoo0NnU8erA",
    description="The slots are classified as TP/FP/FN based on the type match, overlap percentage, \
                orientation difference and center distance. Rates are calculated based on the classification.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class SISlotOfferRateCAEdge(TestCase):
    """TP SlotOffer test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            TPTestStepCAEdge,
            FPTestStepCAEdge,
            FNTestStepCAEdge,
        ]
