#!/usr/bin/env python3
"""TRJCTL TestCases for Regression in CI."""

import logging

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

import os
import sys

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
from pl_parking.PLP.MF.TRJCTL.ft_trjctl import TestStepFtParkingTrajctl, TestStepFtParkingTrajctl2

signals_obj = MfSignals()

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

Test_Case_Alias = "MF_TRJCTL"
TEST_CASE_NAME = "MF TRJCTL"


EXPECTED_RESULT_parLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parLeft(TestStepFtParkingTrajctl):
    """Parallel Left Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_parLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_parLeft(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_parLeft(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parLeft, Step_2_parLeft]


EXPECTED_RESULT_parRight = ">= 90 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parRight(TestStepFtParkingTrajctl):
    """Parallel Right Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_parRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_parRight(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_parRight(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parRight, Step_2_parRight]


EXPECTED_RESULT_perpLeft = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpLeft(TestStepFtParkingTrajctl):
    """Perpendicular Left Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_perpLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_perpLeft(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_perpLeft(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpLeft, Step_2_perpLeft]


EXPECTED_RESULT_perpRight = ">= 93 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpRight(TestStepFtParkingTrajctl):
    """Perpendicular Right Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_perpRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_perpRight(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_perpRight(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpRight, Step_2_perpRight]


EXPECTED_RESULT_angLeft = ">= 91 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angLeft(TestStepFtParkingTrajctl):
    """Angular Left Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_angLeft,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_angLeft(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_angLeft(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angLeft, Step_2_angLeft]


EXPECTED_RESULT_angRight = ">= 90 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angRight(TestStepFtParkingTrajctl):
    """Angular Right Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_angRight,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_angRight(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_angRight(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angRight, Step_2_angRight]


EXPECTED_RESULT_parLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parLeft_small(TestStepFtParkingTrajctl):
    """Parallel Left small Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_parLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_parLeft_small(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_parLeft_small(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parLeft_small, Step_2_parLeft_small]


EXPECTED_RESULT_parRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_parRight_small(TestStepFtParkingTrajctl):
    """Parallel Right small Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_parRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_parRight_small(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_parRight_small(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_parRight_small, Step_2_parRight_small]


EXPECTED_RESULT_perpLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpLeft_small(TestStepFtParkingTrajctl):
    """Perpendicular Left small Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_perpLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_perpLeft_small(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_perpLeft_small(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpLeft_small, Step_2_perpLeft_small]


EXPECTED_RESULT_perpRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_perpRight_small(TestStepFtParkingTrajctl):
    """Perpendicular Right small Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_perpRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_perpRight_small(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_perpRight_small(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_perpRight_small, Step_2_perpRight_small]


EXPECTED_RESULT_angLeft_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angLeft_small(TestStepFtParkingTrajctl):
    """Angular Left smallt Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_angLeft_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_angLeft_small(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_angLeft_small(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angLeft_small, Step_2_angLeft_small]


EXPECTED_RESULT_angRight_small = "= 100 %"


@teststep_definition(
    step_number=1,
    name="TRJCTL 1",
    description=(
        "Check that orientation error, current deviation, vehicle speed and vehicle acceleration are within thresholds"
        " (check is done after apStates == 3 until the end of the simulation."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_1_angRight_small(TestStepFtParkingTrajctl):
    """Angular Right small Test Step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        super().process()
        self.result.measured_result = fh.return_result(self.test_result)


@teststep_definition(
    step_number=2,
    name="TRJCTL 2",
    description=(
        " Check that target pose deviation signals are below defined thresholds (check is done after    "
        " AP.targetPosesPort.selectedPoseData.reachedStatus > 0 for 0.8s until end of sim)."
    ),
    expected_result=EXPECTED_RESULT_angRight_small,
)
@register_signals(Test_Case_Alias, MfSignals)
class Step_2_angRight_small(TestStepFtParkingTrajctl2):
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
        "Check if the KPI for TRJCTL is passed between 'AP.planningCtrlPort.apStates       "
        " ' == 3 and end of sim.         Check if the KPI for TRJCTL is passed between"
        " 'AP.targetPosesPort.selectedPoseData.reachedStatus' >0        for 0.8 s and end of sim."
    ),
)
class FtParkingTrajctl_angRight_small(TestCase):
    """TRJCTL Test Case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [Step_1_angRight_small, Step_2_angRight_small]
