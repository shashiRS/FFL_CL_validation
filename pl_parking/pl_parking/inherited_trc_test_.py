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
from tsf.core.report import CustomReportOverview
from tsf.io.bsig import BsigWriter
from tsf.io.signals import SignalDefinition, SignalReader
from tsf.testbench._internals.report import Report
from tsf.testbench._internals.report_common import TestrunContainer

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

EXAMPLE = "example"


# This class `CustomOverview` is a subclass of `CustomReportOverview` in Python.
class CustomOverview(CustomReportOverview):
    """Custom Overview Class"""

    def build(self, testrun_container: TestrunContainer) -> str:
        """# noqa: D402
        The build function is called by the testrun_container.build() function.
        It should return a string containing the HTML code for the report section.

        :param self: Access the instance of the class
        :param testrun_container: TestrunContainer: Access the testrun container
        :return: A string, which is then added to the report
        """
        from collections import defaultdict

        d = defaultdict(dict)

        for _, tc_ctr in testrun_container.testcase_containers.items():
            for _, ts_ctr in tc_ctr.teststep_containers.items():
                for result in ts_ctr.teststep_results:
                    m_res = result.measured_result
                    e_res = result.teststep_definition.expected_results[None]
                    (
                        _,
                        status,
                    ) = e_res.compute_result_status(m_res)
                    verdict = status.key.lower()
                    d[result.collection_entry.name][tc_ctr.testcase_definition.name] = {"Result": verdict}

        with open(os.path.join(self.environment.output_folder, "functional_test_results.json"), "w") as outfile:
            import json

            json.dump(d, outfile, indent=4)

        r = """
                     <p> <a href="functional_test_results.json" download="functional_test_results.json">
                <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-download" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path fill-rule="evenodd" d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
          <path fill-rule="evenodd" d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
        </svg>
                JSON</a>
                </p>
                    """

        return r


class ExampleSignals(SignalDefinition):
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
    exp_sd = ExampleSignals()
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
        wrt[exp_sd.signal_properties[ExampleSignals.Columns.ACTIVATION_A].signals[0]] = sig_a
        wrt[exp_sd.signal_properties[ExampleSignals.Columns.ACTIVATION_B].signals[0]] = sig_b
        wrt[exp_sd.signal_properties[ExampleSignals.Columns.ACTIVATION_D].signals[0]] = sig_d
        wrt[exp_sd.signal_properties[ExampleSignals.Columns.BINARY_ACTIVATION_A].signals[0]] = binary_activation_a
        wrt[exp_sd.signal_properties[ExampleSignals.Columns.BINARY_ACTIVATION_B].signals[0]] = binary_activation_b
        wrt[exp_sd.signal_properties[ExampleSignals.Columns.EGO_VELO].signals[0]] = ego_vx


@teststep_definition(
    step_number=1,
    name="Check for some_activation_a",
    description="Example for checking the activation of 'some_activation_a' signal",
    expected_result="> 80 %",
)
@register_signals(EXAMPLE, ExampleSignals)
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
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        _log.debug("Starting processing...")

        example_signals = self.readers[EXAMPLE].signals

        activation = example_signals.loc[(example_signals[ExampleSignals.Columns.ACTIVATION_A] != 0)]

        if len(activation) == 0:
            self.result.measured_result = Result(0, unit="%")  # Setting 0 fails the teststep
            return

        self.result.measured_result = Result(100.0, unit="%")  # Setting 100 passes the teststep


@verifies("req-001")
@testcase_definition(
    name="Minimal example",
    description="The most basic TSF example.",
)
@register_inputs("/Playground_2/TSF-Debug")
# @register_inputs("/TSF_DEBUG/")
class ExampleMinimalTestCase(TestCase):
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

    _, testrun_id, cp = debug(
        ExampleMinimalTestCase,
        *test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )
    return testrun_id, cp


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    testrun_id, cp = main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)

    run_spec = out_folder / "run_spec.json"
    report = Report(
        testrun_id,
        Path(os.path.join(out_folder, "report")),
        out_folder,
        run_spec,
        development_details=True,
        connection_provider=cp,
        redo_all=True,
        from_hpc_preprocessing=True,
        is_regression=False,
        overview_plugins=[
            "pl_parking.minimal_example.CustomOverview",
        ],
    )

    report.make_all()
    _log.debug("All done.")
