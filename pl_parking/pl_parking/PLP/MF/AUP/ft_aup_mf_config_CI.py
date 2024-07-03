#!/usr/bin/env python3
"""AupCore TestCases for Regression in CI."""

import os
import sys

from tsf.core.testcase import (
    TestCase,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))  # nopep8
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)
import pl_parking.common_ft_helper as fh  # nopep8
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfSignals
from pl_parking.PLP.MF.AUP.ft_aup_core import (
    AupCoreET1ET5Test,
    AupCoreET2ET5Test,
    AupCoreET2FirstTest,
    AupCoreET2SecondTest,
    AupCoreET3ET5Test,
    AupCoreET4ET5Test,
)

__author__ = "<CHANGE ME>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


Test_Case_Alias = "MF_AUP_CORE"
TEST_CASE_NAME = "MF AUP CORE"

EXPECTED_RESULT_parLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parLeft(AupCoreET2FirstTest):
    """Parallel Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_parLeft(AupCoreET2SecondTest):
    """Parallel Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_parLeft(AupCoreET1ET5Test):
    """Parallel Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_parLeft(AupCoreET2ET5Test):
    """Parallel Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_parLeft(AupCoreET3ET5Test):
    """Parallel Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_parLeft(AupCoreET4ET5Test):
    """Parallel Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_parLeft(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_parLeft,
            Step_2_parLeft,
            Step_3_parLeft,
            Step_4_parLeft,
            Step_5_parLeft,
            Step_6_parLeft,
        ]


EXPECTED_RESULT_parRight = ">= 81.0 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parRight(AupCoreET2FirstTest):
    """Parallel Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_parRight(AupCoreET2SecondTest):
    """Parallel Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_parRight(AupCoreET1ET5Test):
    """Parallel Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_parRight(AupCoreET2ET5Test):
    """Parallel Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_parRight(AupCoreET3ET5Test):
    """Parallel Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_parRight(AupCoreET4ET5Test):
    """Parallel Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_parRight(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_parRight,
            Step_2_parRight,
            Step_3_parRight,
            Step_4_parRight,
            Step_5_parRight,
            Step_6_parRight,
        ]


EXPECTED_RESULT_perpLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpLeft(AupCoreET2FirstTest):
    """Perpendicular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_perpLeft(AupCoreET2SecondTest):
    """Perpendicular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_perpLeft(AupCoreET1ET5Test):
    """Perpendicular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_perpLeft(AupCoreET2ET5Test):
    """Perpendicular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_perpLeft(AupCoreET3ET5Test):
    """Perpendicular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_perpLeft(AupCoreET4ET5Test):
    """Perpendicular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_perpLeft(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_perpLeft,
            Step_2_perpLeft,
            Step_3_perpLeft,
            Step_4_perpLeft,
            Step_5_perpLeft,
            Step_6_perpLeft,
        ]


EXPECTED_RESULT_perpRight = ">= 88.0 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpRight(AupCoreET2FirstTest):
    """Perpendicular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_perpRight(AupCoreET2SecondTest):
    """Perpendicular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_perpRight(AupCoreET1ET5Test):
    """Perpendicular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_perpRight(AupCoreET2ET5Test):
    """Perpendicular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_perpRight(AupCoreET3ET5Test):
    """Perpendicular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_perpRight(AupCoreET4ET5Test):
    """Perpendicular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_perpRight(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_perpRight,
            Step_2_perpRight,
            Step_3_perpRight,
            Step_4_perpRight,
            Step_5_perpRight,
            Step_6_perpRight,
        ]


EXPECTED_RESULT_angLeft = ">= 90 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angLeft(AupCoreET2FirstTest):
    """Angular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_angLeft(AupCoreET2SecondTest):
    """Angular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_angLeft(AupCoreET1ET5Test):
    """Angular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_angLeft(AupCoreET2ET5Test):
    """Angular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_angLeft(AupCoreET3ET5Test):
    """Angular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_angLeft(AupCoreET4ET5Test):
    """Angular Left Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_angLeft(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_angLeft,
            Step_2_angLeft,
            Step_3_angLeft,
            Step_4_angLeft,
            Step_5_angLeft,
            Step_6_angLeft,
        ]


# parrigh

EXPECTED_RESULT_angRight = ">= 86 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angRight(AupCoreET2FirstTest):
    """Angular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_angRight(AupCoreET2SecondTest):
    """Angular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_angRight(AupCoreET1ET5Test):
    """Angular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_angRight(AupCoreET2ET5Test):
    """Angular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_angRight(AupCoreET3ET5Test):
    """Angular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_angRight(AupCoreET4ET5Test):
    """Angular Right Test Step."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_angRight(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_angRight,
            Step_2_angRight,
            Step_3_angRight,
            Step_4_angRight,
            Step_5_angRight,
            Step_6_angRight,
        ]


EXPECTED_RESULT_parLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parLeft_small(AupCoreET2FirstTest):
    """Parallel Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_parLeft_small(AupCoreET2SecondTest):
    """Parallel Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_parLeft_small(AupCoreET1ET5Test):
    """Parallel Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_parLeft_small(AupCoreET2ET5Test):
    """Parallel Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_parLeft_small(AupCoreET3ET5Test):
    """Parallel Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_parLeft_small(AupCoreET4ET5Test):
    """Parallel Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_parLeft_small(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_parLeft_small,
            Step_2_parLeft_small,
            Step_3_parLeft_small,
            Step_4_parLeft_small,
            Step_5_parLeft_small,
            Step_6_parLeft_small,
        ]


EXPECTED_RESULT_parRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parRight_small(AupCoreET2FirstTest):
    """Parallel Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_parRight_small(AupCoreET2SecondTest):
    """Parallel Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_parRight_small(AupCoreET1ET5Test):
    """Parallel Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_parRight_small(AupCoreET2ET5Test):
    """Parallel Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_parRight_small(AupCoreET3ET5Test):
    """Parallel Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_parRight_small(AupCoreET4ET5Test):
    """Parallel Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_parRight_small(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_parRight_small,
            Step_2_parRight_small,
            Step_3_parRight_small,
            Step_4_parRight_small,
            Step_5_parRight_small,
            Step_6_parRight_small,
        ]


EXPECTED_RESULT_perpLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpLeft_small(AupCoreET2FirstTest):
    """Perpendicular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_perpLeft_small(AupCoreET2SecondTest):
    """Perpendicular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_perpLeft_small(AupCoreET1ET5Test):
    """Perpendicular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_perpLeft_small(AupCoreET2ET5Test):
    """Perpendicular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_perpLeft_small(AupCoreET3ET5Test):
    """Perpendicular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_perpLeft_small(AupCoreET4ET5Test):
    """Perpendicular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_perpLeft_small(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_perpLeft_small,
            Step_2_perpLeft_small,
            Step_3_perpLeft_small,
            Step_4_perpLeft_small,
            Step_5_perpLeft_small,
            Step_6_perpLeft_small,
        ]


EXPECTED_RESULT_perpRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpRight_small(AupCoreET2FirstTest):
    """Perpendicular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_perpRight_small(AupCoreET2SecondTest):
    """Perpendicular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_perpRight_small(AupCoreET1ET5Test):
    """Perpendicular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_perpRight_small(AupCoreET2ET5Test):
    """Perpendicular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_perpRight_small(AupCoreET3ET5Test):
    """Perpendicular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_perpRight_small(AupCoreET4ET5Test):
    """Perpendicular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_perpRight_small(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_perpRight_small,
            Step_2_perpRight_small,
            Step_3_perpRight_small,
            Step_4_perpRight_small,
            Step_5_perpRight_small,
            Step_6_perpRight_small,
        ]


EXPECTED_RESULT_angLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angLeft_small(AupCoreET2FirstTest):
    """Angular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_angLeft_small(AupCoreET2SecondTest):
    """Angular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_angLeft_small(AupCoreET1ET5Test):
    """Angular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_angLeft_small(AupCoreET2ET5Test):
    """Angular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_angLeft_small(AupCoreET3ET5Test):
    """Angular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_angLeft_small(AupCoreET4ET5Test):
    """Angular Left Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_angLeft_small(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_angLeft_small,
            Step_2_angLeft_small,
            Step_3_angLeft_small,
            Step_4_angLeft_small,
            Step_5_angLeft_small,
            Step_6_angLeft_small,
        ]


EXPECTED_RESULT_angRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="Maneuver Check",
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START) to"
        "reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required"
        "speed (V_MIN = 0.002777778)."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angRight_small(AupCoreET2FirstTest):
    """Angular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="Maneuver Completion Time Check",
    description=(
        "Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and MANEUVER_FINISHED(5) were found)              "
        "   in less than 200.0 seconds(T_SIM_MAX)."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_angRight_small(AupCoreET2SecondTest):
    """Angular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=3,
    name="Simulation Time Check",
    description=(
        "Verify that the simulation time does not exceed the maximum time, maneuver has not been              "
        "   interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than          "
        "       maximum accepted."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_3_angRight_small(AupCoreET1ET5Test):
    """Angular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=4,
    name="Number of Strokes Threshold check",
    description=(
        "Verify that after the maneuver has begun, the number of strokes does not exceed maximum accepted              "
        "   number of strokes."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_4_angRight_small(AupCoreET2ET5Test):
    """Angular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=5,
    name="Acceleration and Speed Threshold Check",
    description=(
        "Check that after Planning control port is equal to 3, the maximum acceleration and speed does not             "
        "    exceed accepted values."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_5_angRight_small(AupCoreET3ET5Test):
    """Angular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=6,
    name="Position Check",
    description="Check that after the target has reached the desired position, no deviations are present.",
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_6_angRight_small(AupCoreET4ET5Test):
    """Angular Right Test Step for small regr."""

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@verifies("req-001")
@testcase_definition(
    name=TEST_CASE_NAME,
    description=(
        "Verify that when the maneuver has begun, it takes less than 10.0 seconds (T_SIM_MAX_START)                 to"
        " reach the minimum required steering angle(STEER_ANGLE_REQ_MIN = 0.1) OR minimum required                "
        " speed (V_MIN = 0.002777778).                 Verify that the maneuver was completed (MANEUVER_ACTIVE(17) and"
        " MANEUVER_FINISHED(5) were found)                 in less than 200.0 seconds(T_SIM_MAX).                "
        " Verify that for the whole parking, the duration has not exceeded max time, maneuver has not been             "
        "    interrupted, no error messages appeared, space has not been exceeded and cycle time is lower than         "
        "        maximum accepted.                 Verify that after the maneuver has begun, the number of strokes does"
        " not exceed maximum accepted                 number of strokes.                 Check that after Planning"
        " control port is equal to 3, the maximum acceleration and speed does not                 exceed accepted"
        " values.                 Check that after the target has reached the desired position, no deviations are"
        " present."
    ),
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class MF_AUP_CORE_angRight_small(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            Step_1_angRight_small,
            Step_2_angRight_small,
            Step_3_angRight_small,
            Step_4_angRight_small,
            Step_5_angRight_small,
            Step_6_angRight_small,
        ]
