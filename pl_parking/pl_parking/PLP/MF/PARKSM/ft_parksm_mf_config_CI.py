"""PARKSM TestCases for Regression in CI."""

import logging
import os
import sys

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
from tsf.core.testcase import (
    TestCase,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfSignals
from pl_parking.PLP.MF.PARKSM.ft_parksm import TestStepFtParkingParkSM

__author__ = "<CHANGE ME>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

Test_Case_Alias = "MF_PARKSM"
TEST_CASE_NAME = "MF PARKSM"


EXPECTED_RESULT_parLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parLeft(TestStepFtParkingParkSM):
    """Parallel Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_parLeft(TestCase):
    """Parallel Left test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parLeft]


EXPECTED_RESULT_parRight = ">= 92 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parRight(TestStepFtParkingParkSM):
    """Parallel Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_parRight(TestCase):
    """Parallel Right test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_parRight]


EXPECTED_RESULT_perpLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpLeft(TestStepFtParkingParkSM):
    """Perpendicular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_perpLeft(TestCase):
    """Perpendicular Left test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_perpLeft]


EXPECTED_RESULT_perpRight = ">= 93 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpRight(TestStepFtParkingParkSM):
    """Perpendicular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_perpRight(TestCase):
    """Perpendicular Right Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_perpRight]


EXPECTED_RESULT_angLeft = ">= 91 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angLeft(TestStepFtParkingParkSM):
    """Angular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_angLeft(TestCase):
    """Angular Left Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_angLeft]


EXPECTED_RESULT_angRight = ">= 90 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angRight(TestStepFtParkingParkSM):
    """Angular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_angRight(TestCase):
    """Angular Right Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_angRight]


EXPECTED_RESULT_parLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parLeft_small(TestStepFtParkingParkSM):
    """Parallel Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_parLeft_small(TestCase):
    """Parallel Left test case for small regr."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_parLeft_small]


EXPECTED_RESULT_parRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parRight_small(TestStepFtParkingParkSM):
    """Parallel Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_parRight_small(TestCase):
    """Parallel Right test case for small regr."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_parRight_small]


EXPECTED_RESULT_perpLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpLeft_small(TestStepFtParkingParkSM):
    """Perpendicular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_perpLeft_small(TestCase):
    """Perpendicular Left test case for small regr."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_perpLeft_small]


EXPECTED_RESULT_perpRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpRight_small(TestStepFtParkingParkSM):
    """PerpendicularRight Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_perpRight_small(TestCase):
    """Perpendicular Right test case for small regr."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_perpRight_small]


EXPECTED_RESULT_angLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angLeft_small(TestStepFtParkingParkSM):
    """Angular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_angLeft_small(TestCase):
    """Angular Left test case for small regr."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_angLeft_small]


EXPECTED_RESULT_angRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="PARKSM",
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angRight_small(TestStepFtParkingParkSM):
    """Angular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Check if it takes less than 200s to start and complete the maneuver. Check if"
        " AP.headUnitVisualizationPort.screen_nu == 17(MANEUVER_ACTIVE) and AP.headUnitVisualizationPort.screen_nu =="
        " 5(MANEUVER_FINISHED) are within 200 s."
    ),
)
class FtParkingParkSM_angRight_small(TestCase):
    """Angular Right Test Case for small regr."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [Step_1_angRight_small]
