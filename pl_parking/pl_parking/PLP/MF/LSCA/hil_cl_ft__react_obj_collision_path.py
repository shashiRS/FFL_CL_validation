"""LSCA react to all objects that are in collision path."""

import logging
import os
import sys

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.mdf import MDFSignalDefinition

import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.PDW.pdw_helper import plotter_helper

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "LSCA_REACT_OBJ_COLLISION_PATH"


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        LSCA_BRAKE_REQ = "Lsca_brake"
        LSCA_STATE = "Lsca_state"
        T0_uss1_dist = "T0_uss1_dist"
        T0_uss2_dist = "T0_uss2_dist"
        T0_uss3_dist = "T0_uss3_dist"
        T0_uss4_dist = "T0_uss4_dist"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.LSCA_BRAKE_REQ: "MTS.ADAS_CAN.Conti_Veh_CAN.APReq01.LoDMCEmergencyHoldRequest",
            self.Columns.LSCA_STATE: "MTS.MTA_ADC5.MF_LSCA_DATA.statusPort.lscaOverallMode_nu",
            self.Columns.T0_uss1_dist: "CM.Sensor.Object.USS01.Obj.T00.NearPnt.ds_p",
            self.Columns.T0_uss2_dist: "CM.Sensor.Object.USS02.Obj.T00.NearPnt.ds_p",
            self.Columns.T0_uss3_dist: "CM.Sensor.Object.USS03.Obj.T00.NearPnt.ds_p",
            self.Columns.T0_uss4_dist: "CM.Sensor.Object.USS04.Obj.T00.NearPnt.ds_p",
        }


signals_obj = ValidationSignals()


@teststep_definition(
    name="LSCA react to all traffic participants in collision path",
    description="LSCA shall react to all traffic participants on collision course within the Traffic Participant "
    "detection zone within [treaction LSCA]",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class LscaReactTPCollisionPath(TestStep):
    """LscaReactTPCollisionPath Test Step."""

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
        brake_request = signals[ValidationSignals.Columns.LSCA_BRAKE_REQ].tolist()
        t0_uss1_d = signals[ValidationSignals.Columns.T0_uss1_dist].tolist()
        t0_uss2_d = signals[ValidationSignals.Columns.T0_uss2_dist].tolist()
        t0_uss3_d = signals[ValidationSignals.Columns.T0_uss3_dist].tolist()
        t0_uss4_d = signals[ValidationSignals.Columns.T0_uss4_dist].tolist()
        lsca_state = signals[ValidationSignals.Columns.LSCA_STATE].tolist()
        trigger0 = 0
        trigger1 = 0
        early_br_rq = 0
        self.result.measured_result = None
        det_zone_fr = None

        for fr in range(0, len(time)):
            if not trigger0:
                if lsca_state[fr] == constants.HilCl.Lsca.LSCA_ACTIVE:
                    trigger0 = 1
            elif (
                0 < t0_uss1_d[fr] <= constants.HilCl.Lsca.MAX_FRONT_DETECTION_ZONE
                or 0 < t0_uss2_d[fr] <= constants.HilCl.Lsca.MAX_FRONT_DETECTION_ZONE
                or 0 < t0_uss3_d[fr] <= constants.HilCl.Lsca.MAX_FRONT_DETECTION_ZONE
                or 0 < t0_uss4_d[fr] <= constants.HilCl.Lsca.MAX_FRONT_DETECTION_ZONE
            ):
                trigger1 = 1
                det_zone_fr = fr
                break
            else:
                if brake_request[fr]:
                    # break request before static object entered in detection zone
                    self.result.measured_result = FALSE
                    early_br_rq = 1

        if trigger1:
            reaction_time = 0
            for fr in range(det_zone_fr, len(time)):
                if reaction_time < constants.HilCl.Lsca.T_REACTION_LSCA:
                    if brake_request[fr]:
                        self.result.measured_result = TRUE
                    if fr == (len(time) - 1):
                        self.result.measured_result = FALSE
                    reaction_time = (time[fr] - time[det_zone_fr]) / 1000
                else:
                    if self.result.measured_result is None:
                        self.result.measured_result = FALSE
                        break

        if not trigger0:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.LSCA_STATE]} did not take value"
                f"{constants.HilCl.Lsca.LSCA_ACTIVE}.".split()
            )
            signal_summary["LSCA was not active"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif not trigger1:
            evaluation = " ".join(
                f"None of the following signals took values between 0 and 6 m:<br>"
                f"{signals_obj._properties[ValidationSignals.Columns.T0_uss1_dist]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.T0_uss2_dist]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.T0_uss3_dist]}, <br>"
                f"{signals_obj._properties[ValidationSignals.Columns.T0_uss4_dist]}, <br>".split()
            )
            signal_summary["No static object entered the detection zone"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
            self.result.measured_result = FALSE
        elif self.result.measured_result == FALSE:
            if early_br_rq:
                evaluation = " ".join(
                    f"{signals_obj._properties[ValidationSignals.Columns.LSCA_BRAKE_REQ]} signal  took value 1"
                    f"before one of the following signals took values between 0 and 6:"
                    f"{signals_obj._properties[ValidationSignals.Columns.T0_uss1_dist]}, <br>"
                    f"{signals_obj._properties[ValidationSignals.Columns.T0_uss2_dist]}, <br>"
                    f"{signals_obj._properties[ValidationSignals.Columns.T0_uss3_dist]}, <br>"
                    f"{signals_obj._properties[ValidationSignals.Columns.T0_uss4_dist]}, <br>".split()
                )
                signal_summary["Brake request went to 1 before TP entered in detection zone"] = evaluation
            else:
                evaluation = " ".join(
                    f"{signals_obj._properties[ValidationSignals.Columns.LSCA_BRAKE_REQ]} signal did not took"
                    f" value 1 in maximum {constants.HilCl.Lsca.T_REACTION_LSCA} [ms]. ".split()
                )
                signal_summary["LSCA did not react to traffic participant on collision course. "] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )
        elif self.result.measured_result == TRUE:
            evaluation = " ".join(
                f"{signals_obj._properties[ValidationSignals.Columns.LSCA_BRAKE_REQ]} signal took value 1"
                f"in less than {constants.HilCl.Lsca.T_REACTION_LSCA} [ms]".split()
            )
            signal_summary["LSCA reacted to traffic participant on collision course"] = evaluation
            self.result.details["Plots"].append(
                fh.convert_dict_to_pandas(signal_summary=signal_summary, table_header_left="Evaluation")
            )

        columns = [
            ValidationSignals.Columns.LSCA_BRAKE_REQ,
            ValidationSignals.Columns.LSCA_STATE,
            ValidationSignals.Columns.T0_uss1_dist,
            ValidationSignals.Columns.T0_uss2_dist,
            ValidationSignals.Columns.T0_uss3_dist,
            ValidationSignals.Columns.T0_uss4_dist,
        ]
        fig = plotter_helper(time, signals, columns, signals_obj._properties)
        fig.update_layout(title="Signals used in evaluation")
        self.result.details["Plots"].append(fig.to_html(full_html=False, include_plotlyjs=False))


@verifies(
    requirement="2939372",
    doors_url="https://jazz.conti.de/rm4/resources/BI_0cqfkastEe-h96jyDYWsSA?oslc_config.context=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
)
@testcase_definition(
    name="LSCA react to all traffic participants in collision path",
    description="LSCA shall react to all traffic participants on collision course within the Traffic Participant "
    "detection zone within [treaction LSCA]",
)
class LscaReactTPCollisionPathTestCase(TestCase):
    """LscaReactTPCollisionPath test case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [
            LscaReactTPCollisionPath,
        ]
