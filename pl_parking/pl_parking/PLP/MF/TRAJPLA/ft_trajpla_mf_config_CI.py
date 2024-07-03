#!/usr/bin/env python3
"""TRAJPLA TestCases for Regression in CI."""

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
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals
from pl_parking.PLP.MF.TRAJPLA.ft_trajpla import TestStepFtParkingTrajpla

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

Test_Case_Alias = "MF_TRAJPLA"
TEST_CASE_NAME = "MF TRAJPLA"

EXPECTED_RESULT_parLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parLeft(TestStepFtParkingTrajpla):
    """Parallel Left Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_parLeft(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parLeft]


EXPECTED_RESULT_parRight = ">= 83.0 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parRight(TestStepFtParkingTrajpla):
    """Parallel Right Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_parRight(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parRight]


EXPECTED_RESULT_perpLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpLeft(TestStepFtParkingTrajpla):
    """Perpendicular Left Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_perpLeft(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpLeft]


EXPECTED_RESULT_perpRight = ">= 92.0 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpRight(TestStepFtParkingTrajpla):
    """Perpendicular Right Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_perpRight(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpRight]


EXPECTED_RESULT_angLeft = ">= 91.0 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angLeft(TestStepFtParkingTrajpla):
    """Angular Left Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_angLeft(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angLeft]


EXPECTED_RESULT_angRight = ">= 90.0 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angRight(TestStepFtParkingTrajpla):
    """Angular Right Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_angRight(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angRight]


EXPECTED_RESULT_parLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parLeft_small(TestStepFtParkingTrajpla):
    """Parallel Left small Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_parLeft_small(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parLeft_small]


EXPECTED_RESULT_parRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parRight_small(TestStepFtParkingTrajpla):
    """Parallel Right small Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_parRight_small(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parRight_small]


EXPECTED_RESULT_perpLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpLeft_small(TestStepFtParkingTrajpla):
    """Perpendicular Left small Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_perpLeft_small(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpLeft_small]


EXPECTED_RESULT_perpRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpRight_small(TestStepFtParkingTrajpla):
    """Perpendicular Right small Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_perpRight_small(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpRight_small]


EXPECTED_RESULT_angLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angLeft_small(TestStepFtParkingTrajpla):
    """Angular Left small Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_angLeft_small(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angLeft_small]


EXPECTED_RESULT_angRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRAJPLA",
    description=(
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angRight_small(TestStepFtParkingTrajpla):
    """Angular Right small Test Step."""

    custom_report = MfCustomTeststepReport

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
        "Check that after Planning control port is 3, the speed does not exceed the accepted value, number of strokes"
        " does not exceed the maximum accepted value and number of curvature steps is 0."
    ),
)
class FtParkingTrajpla_angRight_small(TestCase):
    """TRAJPLA Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angRight_small]
