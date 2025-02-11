"""Example functional test"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

"""imports from current repo"""
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "PDW_INSIDE_FRONT"

gearPosition = constants.GearReqConstants
pdwState = constants.SilCl.PDWConstants.pdwState
pdwSysState = constants.SilCl.PDWConstants.pdwSystemState
pdw_hmi_interact = constants.SilCl.PDWConstants.pdwUserActionHeadUnit  # TAP_ON_PDC = 35
drvTubeDisplay = constants.SilCl.PDWConstants.DrivingTubeReq
wheel_direction = constants.SilCl.PDWConstants.WheelDirection
dt_intersection = constants.SilCl.PDWConstants.IntersectsDrvTube
speed_converter = 3.6  # vehicle velocity convert factor unit [km/h]
overspeed_deact = 20  # km/h


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        PDW_SYSTEM_STATE = "PDWSystemState"
        PDW_STATE = "PDWSate"
        VELOCITY = "Velocity"
        STEERING_ANGLE = "SteeringAngle"
        TIME = "Time"
        TAP_ON_HMI = "UserActionHMI"
        GEARBOX_STATE = "GearBoxState"
        DRV_TUBE = "DrvTubeDisplay"
        OBSTACE_DISTANCE1 = "EvalShortDist1"

        INTERSECTS_SECTORFR = "INTERSECTS_SECTORFR{}"
        INTERSECTS_SECTORFR0 = "INTERSECTS_SECTORFR0"
        INTERSECTS_SECTORFR1 = "INTERSECTS_SECTORFR1"
        INTERSECTS_SECTORFR2 = "INTERSECTS_SECTORFR2"
        INTERSECTS_SECTORFR3 = "INTERSECTS_SECTORFR3"

        SECTOR_DISTANCEFR = "SECTOR_DISTANCEFR{}"
        SECTOR_DISTANCEFR0 = "SECTOR_DISTANCEFR0"
        SECTOR_DISTANCEFR1 = "SECTOR_DISTANCEFR1"
        SECTOR_DISTANCEFR2 = "SECTOR_DISTANCEFR2"
        SECTOR_DISTANCEFR3 = "SECTOR_DISTANCEFR3"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "PDW_Signals",
        ]

        self._properties = {
            self.Columns.PDW_SYSTEM_STATE: "AP.drvWarnStatus.pdwSystemState_nu",
            self.Columns.PDW_STATE: "AP.drvWarnStatus.pdwState_nu",
            self.Columns.VELOCITY: "Car.v",
            self.Columns.TIME: "Time",
            self.Columns.TAP_ON_HMI: "AP.hmiOutputPort.userActionHeadUnit_nu",
            self.Columns.GEARBOX_STATE: "AP.odoInputPort.odoSigFcanPort.gearboxCtrlStatus.gearCur_nu",
            self.Columns.DRV_TUBE: "AP.pdcpDrivingTubePort.drvTubeDisplay_nu",
            self.Columns.OBSTACE_DISTANCE1: "AP.testEvaluation.shortestDistanceCM[1]",
        }

        intersect_sectors_front = {
            self.Columns.INTERSECTS_SECTORFR.format(x): f"AP.pdcpSectorsPort.sectorsFront_{x}.intersectsDrvTube_nu"
            for x in range(4)
        }
        front_sectors_distance = {
            self.Columns.SECTOR_DISTANCEFR.format(x): f"AP.pdcpSectorsPort.sectorsFront_{x}.smallestDistance_m"
            for x in range(4)
        }

        self._properties.update(intersect_sectors_front)
        self._properties.update(front_sectors_distance)


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="Intersects Driving Tube Front",  # this would be shown as a test step name in html report
    description=(
        "This test step evaluates if front sectors are inside the driving tube."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class IntersectsDrvTubeFront(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
    """

    custom_report = MfCustomTeststepReport  # Specific overview

    def __init__(self):
        super().__init__()

    #
    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """  # required docstring
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        # Make a constant with the reader for signals:
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_summary = {}
        signals = self.readers[ALIAS]  # Make a dataframe(df) with all signals extracted from Signals class

        self.velocity = signals[Signals.Columns.VELOCITY]
        self.ap_time = signals[Signals.Columns.TIME]
        self.pdw_state = signals[Signals.Columns.PDW_STATE]
        self.pdw_sys_state = signals[Signals.Columns.PDW_SYSTEM_STATE]
        self.dt_req = signals[Signals.Columns.DRV_TUBE]
        self.hmi_interact = signals[Signals.Columns.TAP_ON_HMI]
        self.short_dist_1 = signals[Signals.Columns.OBSTACE_DISTANCE1]

        self.intersect_sector_f0 = signals[Signals.Columns.INTERSECTS_SECTORFR0]
        self.intersect_sector_f1 = signals[Signals.Columns.INTERSECTS_SECTORFR1]
        self.intersect_sector_f2 = signals[Signals.Columns.INTERSECTS_SECTORFR2]
        self.intersect_sector_f3 = signals[Signals.Columns.INTERSECTS_SECTORFR3]

        self.smallest_dist_fr_0 = signals[Signals.Columns.SECTOR_DISTANCEFR0]
        self.smallest_dist_fr_1 = signals[Signals.Columns.SECTOR_DISTANCEFR1]
        self.smallest_dist_fr_2 = signals[Signals.Columns.SECTOR_DISTANCEFR2]
        self.smallest_dist_fr_3 = signals[Signals.Columns.SECTOR_DISTANCEFR3]

        intersect_sig_name = [
            signals_obj._properties[Signals.Columns.INTERSECTS_SECTORFR0],
            signals_obj._properties[Signals.Columns.INTERSECTS_SECTORFR1],
            signals_obj._properties[Signals.Columns.INTERSECTS_SECTORFR2],
            signals_obj._properties[Signals.Columns.INTERSECTS_SECTORFR3],
        ]
        interact_front = [
            self.intersect_sector_f0,
            self.intersect_sector_f1,
            self.intersect_sector_f2,
            self.intersect_sector_f3,
        ]

        small_dist_fr = [
            self.smallest_dist_fr_0,
            self.smallest_dist_fr_1,
            self.smallest_dist_fr_2,
            self.smallest_dist_fr_3,
        ]

        dist_sign_name = [
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR0],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR1],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR2],
            signals_obj._properties[Signals.Columns.SECTOR_DISTANCEFR3],
        ]

        # Check if PDW activates by button
        idx = -1
        act_btn = False
        verdict = False
        verification = []
        for i, element in enumerate(self.hmi_interact):
            if element == pdw_hmi_interact.TAP_ON_PDC:
                idx = i
                if (
                    self.hmi_interact.iat[idx] == pdw_hmi_interact.TAP_ON_PDC
                    and self.pdw_state.iat[idx] == pdwState.PDW_INT_STATE_ACT_BTN
                    and self.pdw_sys_state.iat[idx] == pdwSysState.PDW_ACTIVATED_BY_BUTTON
                ):
                    act_btn = True
                    break
        idx_drt = idx
        if act_btn:
            # Check if Driving tube is in front direction
            for j, element in enumerate(self.dt_req):
                if element == drvTubeDisplay.PDC_DRV_TUBE_FRONT:
                    idx_drt = j
                    verdict = True
                    break
                else:
                    verdict = False

        idx_int = -1
        if verdict and self.dt_req.iat[idx_drt] == drvTubeDisplay.PDC_DRV_TUBE_FRONT:
            for k in range(4):
                for i, element in enumerate(small_dist_fr[k]):
                    if element == min(small_dist_fr[k]):
                        idx_int = i
                        break
                    if interact_front[k].iat[idx_int] == dt_intersection.INTERSECTS:
                        verification.append(True)
                    else:
                        verification.append(False)
            if False in verification:
                for x in range(4):
                    signal_summary[intersect_sig_name[x]] = (
                        f"The Driving Tube does not intersects with the most critical slice of the sector with value = {int(interact_front[x].iat[idx_int])}(intersectsDrvTube_nu)"
                    )
                verdict = False
            else:
                verdict = True
                for x in range(4):
                    signal_summary[intersect_sig_name[x]] = (
                        f"The Driving Tube intersects with the most critical slice of the sector with value = {int(interact_front[x].iat[idx_int])}(intersectsDrvTube_nu)"
                    )
        if not act_btn:
            self.result.measured_result = FALSE
            signal_summary["AP.drvWarnStatus.pdwState_nu"] = " PDW function internal state is deactivated."
            signal_summary["AP.drvWarnStatus.pdwSystemState_nu"] = " PDW function system state is OFF."
        else:
            self.result.measured_result = TRUE if verdict else FALSE

        remark = " ".join(
            "intersectsDrvTube: FALSE = 0; TRUE = 1 | Driving tube: PDC_DRV_TUBE_NONE = 0; PDC_DRV_TUBE_FRONT = 1; PDC_DRV_TUBE_REAR = 2".split(),
        )
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fig = go.Figure()
        # add the needed signals in the plot
        fig.add_trace(
            go.Scatter(
                x=self.ap_time,
                y=self.short_dist_1,
                mode="lines",
                name=signals_obj._properties[Signals.Columns.OBSTACE_DISTANCE1],
            )
        )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=interact_front[i],
                    mode="lines",
                    name=signals_obj._properties[Signals.Columns.INTERSECTS_SECTORFR.format(i)],
                )
            )
        for i in range(4):
            fig.add_trace(
                go.Scatter(
                    x=self.ap_time,
                    y=small_dist_fr[i],
                    mode="lines",
                    name=dist_sign_name[i],
                )
            )

        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")
        fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@testcase_definition(
    name="Front Sector intersects Driving Tube",
    description=(
        "PDW function shall determine whether a given sector is inside the driving tube by intersecting the sector's most critical slice with the driving tube when an obstacle is detected inside it."
    ),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class PDWDrvTubeIntersectFront(TestCase):
    """Example test case."""  # required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # required docstring
        return [
            IntersectsDrvTubeFront,
        ]  # in this list all the needed test steps are included
