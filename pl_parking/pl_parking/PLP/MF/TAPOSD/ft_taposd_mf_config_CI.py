#!/usr/bin/env python3
"""TAPOSD TestCases for Regression in CI."""

import os
import sys

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

from tsf.core.testcase import (
    TestCase,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport
from pl_parking.PLP.MF.TAPOSD.ft_taposd import Taposd1, Taposd2

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


Test_Case_Alias = "MF_TAPOSD"
TEST_CASE_NAME = "MF TAPOSD"


EXPECTED_RESULT_parLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_parLeft(Taposd1):
    """Parallel Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_parLeft(Taposd2):
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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_parLeft(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_parLeft,
            Step_2_parLeft,
        ]


EXPECTED_RESULT_parRight = ">= 91.0 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_parRight(Taposd1):
    """Parallel Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_parRight(Taposd2):
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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_parRight(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_parRight,
            Step_2_parRight,
        ]


EXPECTED_RESULT_perpLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_perpLeft(Taposd1):
    """Perpendicular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_perpLeft(Taposd2):
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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_perpLeft(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_perpLeft,
            Step_2_perpLeft,
        ]


EXPECTED_RESULT_perpRight = ">= 93.0 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_perpRight(Taposd1):
    """Perpendicular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_perpRight(Taposd2):
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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_perpRight(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_perpRight,
            Step_2_perpRight,
        ]


EXPECTED_RESULT_angLeft = ">= 91.0 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_angLeft(Taposd1):
    """Angular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_angLeft(Taposd2):
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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_angLeft(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_angLeft,
            Step_2_angLeft,
        ]


EXPECTED_RESULT_angRight = ">= 90.0 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_angRight(Taposd1):
    """Angular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_angRight(Taposd2):
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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_angRight(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_angRight,
            Step_2_angRight,
        ]


EXPECTED_RESULT_parLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_parLeft_small(Taposd1):
    """Parallel Left small Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_parLeft_small(Taposd2):
    """Parallel Left small Test Step."""

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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_parLeft_small(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_parLeft_small,
            Step_2_parLeft_small,
        ]


EXPECTED_RESULT_parRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_parRight_small(Taposd1):
    """Parallel Right small Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_parRight_small(Taposd2):
    """Parallel Right small Test Step."""

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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_parRight_small(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_parRight_small,
            Step_2_parRight_small,
        ]


EXPECTED_RESULT_perpLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_perpLeft_small(Taposd1):
    """Perpendicular Left small Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_perpLeft_small(Taposd2):
    """Perpendicular Left small Test Step."""

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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_perpLeft_small(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_perpLeft_small,
            Step_2_perpLeft_small,
        ]


EXPECTED_RESULT_perpRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_perpRight_small(Taposd1):
    """Perpendicular Right small Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_perpRight_small(Taposd2):
    """Perpendicular Right small Test Step."""

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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_perpRight_small(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_perpRight_small,
            Step_2_perpRight_small,
        ]


EXPECTED_RESULT_angLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_angLeft_small(Taposd1):
    """Angular Left small Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_angLeft_small(Taposd2):
    """Angular Left small Test Step."""

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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_angLeft_small(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_angLeft_small,
            Step_2_angLeft_small,
        ]


EXPECTED_RESULT_angRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TAPOSD 1",
    description=(
        "Check that target pose deviation signals are below defined thresholds (check is done at the end of the"
        " maneuver)."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_1_angRight_small(Taposd1):
    """Angular Right small Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()
        self.step_result = fc.INPUT_MISSING

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TAPOSD 2",
    description="Check that the vehicle is inside defined PB at the end of the maneuver and that there no collisions.",
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, fh.MfSignals)
class Step_2_angRight_small(Taposd2):
    """Angular Right small Test Step."""

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
        "Check that target pose deviation signals are below defined thresholds at the end of measurement and that after"
        " the maneuver finished vehicle is inside defined Parking Box."
    ),
)
class FtParkingTaposd_angRight_small(TestCase):
    """Taposd Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_angRight_small,
            Step_2_angRight_small,
        ]
