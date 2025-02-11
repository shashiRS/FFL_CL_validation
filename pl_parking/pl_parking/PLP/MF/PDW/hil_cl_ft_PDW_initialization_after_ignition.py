"""Park Distance Warning - evaluation script"""

import logging
import os
import sys

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import TestCase, TestStep, register_signals, testcase_definition, teststep_definition, verifies
from tsf.io.mdf import MDFSignalDefinition

import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.PDW.pdw_helper import plotter_helper

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "PDW_INIT_AFTER_IGNITION"


class ValidationSignals(MDFSignalDefinition):
    """Example signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        TIMESTAMP = "mts_ts"
        GEAR_MAN = "Gear_man"
        GEAR_AUT = "Gear_auto"
        PDW_CAN_STATE = "PDW_State"
        VEH_VELOCITY = "Vehicle_velocity"
        IGNITION = "Veh_ignition"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.GEAR_MAN: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActualGear",
            self.Columns.GEAR_AUT: "MTS.ADAS_CAN.Conti_Veh_CAN.Gear.ActGearPos",
            self.Columns.PDW_CAN_STATE: "MTS.AP_Private_CAN.AP_Private_CAN.PDCInfo.PDCSystemState",
            self.Columns.VEH_VELOCITY: "MTS.ADAS_CAN.Conti_Veh_CAN.VehVelocity.VehVelocityExt",
            self.Columns.IGNITION: "MTS.ADAS_CAN.Conti_Veh_CAN.VehInput05.IgnitionOn",
        }


example_obj = ValidationSignals()


@teststep_definition(
    step_number=1,
    name="PDW initialization after ignition",
    description=(
        "The PDW function shall be initialized after ignition ON (time until initial detection of objects "
        "has passed) in less than 1.5s."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class PdwInitAfterIgnitionTS(TestStep):
    """Example test step"""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Process"""
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        signal_summary = {}
        signals = self.readers[SIGNAL_DATA]
        time = signals.index.tolist()
        ig_on_tr_one = 0
        ig_off_tr = 0
        ig_on_tr_two = 0
        ig_two_timestamp = 0
        pdw_state = signals[ValidationSignals.Columns.PDW_CAN_STATE]
        ignition = signals[ValidationSignals.Columns.IGNITION]
        self.result.measured_result = None

        self.result.measured_result = None
        max_time_for_init = 1500000  # 1.5s in us
        time_passed_since_init = 0

        for ts in time:
            if ignition[ts] and not ig_on_tr_one:
                ig_on_tr_one = 1
            if ig_on_tr_one and not ig_off_tr:
                if not ignition[ts]:
                    ig_off_tr = 1
            if ig_off_tr:
                if ignition[ts]:
                    if not ig_on_tr_two:
                        ig_two_timestamp = ts
                        ig_on_tr_two = 1
                    if time_passed_since_init < max_time_for_init:  # 1.5s
                        time_passed_since_init = ts - ig_two_timestamp
                        if pdw_state[ts] == constants.HilCl.PDW.States.OFF:
                            self.result.measured_result = TRUE
                            break
                    else:
                        if self.result.measured_result is None:
                            self.result.measured_result = FALSE

        if ig_on_tr_one == 0:
            evaluation = " ".join(
                f"Ignition signal did not take value " f"of {constants.HilCl.CarMaker.IGNITION_ON}.".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE

        elif ig_off_tr == 0:
            evaluation = " ".join(
                f"Ignition signal: {example_obj._properties[ValidationSignals.Columns.IGNITION]} did not take value of "
                f"{constants.HilCl.CarMaker.IGNITION_OFF} in order to change it to "
                f"{constants.HilCl.CarMaker.IGNITION_ON} again "
                f"We need a second ignition in order to measure correctly 1.5s from ignition start".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE

        elif ig_off_tr == 0:
            evaluation = " ".join(
                f"Evaluation FAILED because ignition signal: "
                f"{example_obj._properties[ValidationSignals.Columns.IGNITION]} did not take "
                f"value of {constants.HilCl.CarMaker.IGNITION_OFF} in order to catch a value change from "
                f"{constants.HilCl.CarMaker.IGNITION_OFF} to {constants.HilCl.CarMaker.IGNITION_ON} for evaluation. "
                f"We need to measure correctly 1.5s from the moment ignition signal: "
                f"{example_obj._properties[ValidationSignals.Columns.IGNITION]} change value from "
                f"{constants.HilCl.CarMaker.IGNITION_OFF} to {constants.HilCl.CarMaker.IGNITION_ON}".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE

        elif ig_on_tr_two:
            evaluation = " ".join(
                f"Evaluation FAILED because ignition signal: "
                f"{example_obj._properties[ValidationSignals.Columns.IGNITION]} did not take value "
                f"1 for the second time".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE

        elif self.result.measured_result == FALSE:
            evaluation = " ".join(
                f"Evaluation FAILED because PDW state signal: "
                f"{example_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} did not change his state to "
                f"{constants.HilCl.PDW.States.OFF} in 1.5 seconds from the moment ignition signal:"
                f"{example_obj._properties[ValidationSignals.Columns.IGNITION]} took value "
                f"{constants.HilCl.CarMaker.IGNITION_ON} for the second time".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"Evaluation PASSED because{example_obj._properties[ValidationSignals.Columns.PDW_CAN_STATE]} changed "
                f"his state to {constants.HilCl.PDW.States.OFF} in 1.5 seconds from the moment"
                f"{example_obj._properties[ValidationSignals.Columns.IGNITION]} took value "
                f"{constants.HilCl.CarMaker.IGNITION_ON} for the second time".split()
            )
            signal_summary["PDW inhibit autoactivation"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        plot_signals = [
            ValidationSignals.Columns.PDW_CAN_STATE,
            ValidationSignals.Columns.IGNITION,
        ]
        fig_fr = plotter_helper(time, signals, plot_signals, example_obj._properties)
        fig_fr.update_layout(title="State and ignition signals")
        self.result.details["Plots"].append(fig_fr.to_html(full_html=False, include_plotlyjs=False))


@verifies(
    requirement="2452112",
    doors_url=r"https://jazz.conti.de/rm4/resources/BI_wiWMgj64Ee-moNw0sxuQRA?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@testcase_definition(
    name="PDW initialization after ignition",
    description="The PDW function shall be initialized after ignition ON (time until initial detection of objects "
    "has passed) in less than 1.5s.",
)
class PDWInitAfterIgnitionTestCase(TestCase):
    """PDW function deactivation by open trunk test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            PdwInitAfterIgnitionTS,
        ]
