#!/usr/bin/env python3
"""
This is most basic example which you can have for TSF.
In this example we are creating a single testcase with a single teststep.
In this would be defining a signal definition and our own bsigs for easy execution.

TRY IT OUT!
Just run the file.
"""

import datetime
import logging
import os
import random
import sys
import tempfile
from pathlib import Path

import numpy as np
import scipy
from tsf.io.bsig import BsigWriter
from tsf.io.signals import SignalDefinition, SignalReader

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.core.utilities import debug
from tsf.db.results import Result

__author__ = "<CHANGE ME>"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

EXAMPLE = "example_1"


class ExampleSignals_1(SignalDefinition):
    """Example signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        ACTIVATION_A = "some_activation_a"
        ACTIVATION_B = "some_activation_b"
        ACTIVATION_D = "some_activation_d"
        BINARY_ACTIVATION_A = "binary_activation_a"
        BINARY_ACTIVATION_B = "binary_activation_b"
        EGO_VELO = "ego_velo"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.ACTIVATION_A: "Example Signal Data.activation.sig_a",
            self.Columns.ACTIVATION_B: "Example Signal Data.activation.sig_b",
            self.Columns.ACTIVATION_D: "Example Signal Data.activation.sig_d",
            self.Columns.BINARY_ACTIVATION_A: "Example Signal Data.aggregation_all.90",
            self.Columns.BINARY_ACTIVATION_B: "Example Signal Data.aggregation_all.50",
            self.Columns.EGO_VELO: "Example Signal Data.ego.velocity.x",
        }


###################################################################
# Note: generate_bsig not relevant for users ######################
###################################################################
def generate_bsig(bsig: Path):
    """Generate a BSIG for the example signal definition."""
    exp_sd = ExampleSignals_1()
    with BsigWriter(bsig) as wrt:
        # timestamps are in microseconds (us) sampling as unit64 data type.
        f = 60e3  # ms
        N = np.random.randint(3000, 8000)
        jitter_max = 3e3  # ms

        # unix timestamp in us
        ts_0 = int(datetime.datetime.utcnow().timestamp() * 1e6)
        ts = np.cumsum(np.ones(N) * f + np.random.randint(0, int(jitter_max), N))
        ts += ts_0
        ts = ts.astype(np.uint64)
        wrt[SignalReader.MTS_TS_SIGNAL] = ts

        sig_a = np.zeros(N)
        samples_a = np.random.randint(1, 10)
        positions = np.random.choice(np.arange(N), samples_a)
        for position in positions:
            sample = np.random.randint(2, 7)
            sig_a[position : position + sample] = 1

        sig_b = np.zeros(N)
        samples_b = np.random.randint(1, 10)
        positions = np.random.choice(np.arange(N), samples_b)
        for position in positions:
            sample = np.random.randint(2, 7)
            sig_b[position : position + sample] = 1

        sig_d = np.zeros(N)
        samples_d = np.random.randint(1, 10)
        positions = np.random.choice(np.arange(N), samples_d)
        for position in positions:
            sample = np.random.randint(2, 7)
            sig_d[position : position + sample] = 1

        # 90% Chance of passing
        binary_activation_a = np.zeros(N)
        if random.random() > 0.02:
            binary_activation_a[N - 1000 : N - 900] = 1

        binary_activation_b = np.zeros(N)
        if random.random() > 0.1:
            binary_activation_b[N - 1000 : N - 900] = 1

        ego_vx = (np.random.random(N) - 0.5) * 0.2
        ego_vx[0] = 0.01
        corners = random.sample(range(1000, N - 1000), 2)
        u = np.zeros(N)
        c0 = min(corners)
        c1 = max(corners) + 2
        # Ramp to 30 km/h
        u[0:c0] = np.arange(c0) * 30 / (3.6 * c0)
        # constant 30 km/h
        u[c0:c1] = np.ones(c1 - c0) * 30 / 3.6
        # ramp down to 0
        u[c1:N] = 30 / 3.6 - np.arange(N - c1) * 30 / (3.6 * (N - c1))
        # mix with ego vx
        ego_vx = ego_vx + u
        ego_vx = scipy.signal.medfilt(ego_vx, 15)

        wrt[SignalReader.MTS_TS_SIGNAL] = ts
        wrt[exp_sd.signal_properties[ExampleSignals_1.Columns.ACTIVATION_A].signals[0]] = sig_a
        wrt[exp_sd.signal_properties[ExampleSignals_1.Columns.ACTIVATION_B].signals[0]] = sig_b
        wrt[exp_sd.signal_properties[ExampleSignals_1.Columns.ACTIVATION_D].signals[0]] = sig_d
        wrt[exp_sd.signal_properties[ExampleSignals_1.Columns.BINARY_ACTIVATION_A].signals[0]] = binary_activation_a
        wrt[exp_sd.signal_properties[ExampleSignals_1.Columns.BINARY_ACTIVATION_B].signals[0]] = binary_activation_b
        wrt[exp_sd.signal_properties[ExampleSignals_1.Columns.EGO_VELO].signals[0]] = ego_vx


@teststep_definition(
    step_number=1,
    name="Check for some_activation_a",
    description="Example for checking the activation of 'some_activation_a' signal",
    expected_result="> 80 %",
)
@register_signals(EXAMPLE, ExampleSignals_1)
class ExampleActivation(TestStep):
    """Example for a testcase that can be tested by a simple pass/fail test.

    Objective
    ---------

    Check every occurrence when signal 'some_activation_a'

    Detail
    ------

    In case there is no signal change to 1 the testcase is failed.
    The test ist performed for all recordings of the collection
    """

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    def process(self):
        """Process data and update result details with plot-related information and the file name of the first artifact."""
        _log.debug("Starting processing...")

        example_signals = self.readers[EXAMPLE].signals

        activation = example_signals.loc[(example_signals[ExampleSignals_1.Columns.ACTIVATION_A] != 0)]

        if len(activation) == 0:
            self.result.measured_result = Result(0, unit="%")  # Setting 0 fails the teststep
            return

        self.result.measured_result = Result(100.0, unit="%")  # Setting 100 passes the teststep


@verifies("req-001")
@testcase_definition(
    name="Minimal example 1",
    description="The most basic TSF example.",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class ExampleMinimalTestCase_1(TestCase):
    """Example test case."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            ExampleActivation,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.
    """
    test_bsigs = [data_folder / f"test_input_{k}.bsig" for k in range(3)]
    os.makedirs(data_folder, exist_ok=True)
    for b in test_bsigs:
        generate_bsig(b)

    debug(
        ExampleMinimalTestCase,  # noqa: F821
        *test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )
    _log.debug("All done.")


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
