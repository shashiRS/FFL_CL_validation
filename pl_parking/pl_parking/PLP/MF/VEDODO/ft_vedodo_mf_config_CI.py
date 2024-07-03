#!/usr/bin/env python3
"""VEDODO TestCases for Regression in CI."""

import os
import sys

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))  # nopep8
if TRC_ROOT not in sys.path:  # nopep8
    sys.path.append(TRC_ROOT)  # nopep8


# nopep8
from tsf.core.testcase import (
    TestCase,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_ft_helper as fh  # nopep8
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,  # nopep8
)
from pl_parking.PLP.MF.VEDODO.ft_vedodoTest import TestStepVedodo

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

Test_Case_Alias = "MF_VEDODO"
TEST_CASE_NAME = "MF VEDODO"


EXPECTED_RESULT_parLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_parLeft(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_parLeft(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parLeft]


EXPECTED_RESULT_parRight = ">= 92 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_parRight(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_parRight(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parRight]


EXPECTED_RESULT_perpLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_perpLeft(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_perpLeft(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpLeft]


EXPECTED_RESULT_perpRight = ">= 93 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_perpRight(TestStepVedodo):
    """Perpendicular Right Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@testcase_definition(
    name=TEST_CASE_NAME,
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_perpRight(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpRight]


EXPECTED_RESULT_angLeft = ">= 91 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_angLeft(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_angLeft(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angLeft]


EXPECTED_RESULT_angRight = ">= 90 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_angRight(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_angRight(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angRight]


EXPECTED_RESULT_parLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_parLeft_small(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_parLeft_small(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parLeft_small]


EXPECTED_RESULT_parRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_parRight_small(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_parRight_small(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parRight_small]


EXPECTED_RESULT_perpLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_perpLeft_small(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_perpLeft_small(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpLeft_small]


EXPECTED_RESULT_perpRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_perpRight_small(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_perpRight_small(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpRight_small]


EXPECTED_RESULT_angLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_angLeft_small(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_angLeft_small(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angLeft_small]


EXPECTED_RESULT_angRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="VEDODO",
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_angRight_small(TestStepVedodo):
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
    description="Verify that absolute error of longitudinal, lateral and yaw deviation are in thresholds",
)
class Vedodo_angRight_small(TestCase):
    """VEDODO Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angRight_small]
