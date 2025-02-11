"""SOTIF, Re-evaluate parking slot"""

import logging
import os
import sys

import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
import itertools

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.mdf import MDFSignalDefinition

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import HilClFuntions, MfHilClCustomTestcaseReport, MfHilClCustomTeststepReport
from pl_parking.PLP.MF.constants import PlotlyTemplate

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "SOTIF_RE_EVAL_SLOT"
__author__ = "uig14850"

signal_ids = [list(range(0, 2)), list(range(0, 3))]


class ValidationSignals(MDFSignalDefinition):
    """Evaluation related signals."""

    class Columns(MDFSignalDefinition.Columns):
        """Definition of the dataframe columns."""

        T00_X = "t00_x"
        T01_X = "t01_x"
        T02_X = "t02_x"
        DYNAMIC_OBJ_X = "Dynamic_obj_x{}"
        DYNAMIC_OBJ_Y = "Dynamic_obj_y{}"
        DYNAMIC_OBJ_SHAPE_ACT_SIZE = "Dynamic_obj_shape_act_size{}"
        NUMBER_OF_DYNAMIC_OBJS = "Number_of_dynamic_objects"
        CAR_TX = "Car_tx"
        CAR_TY = "Car_ty"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.T00_X: "CM.Traffic.T00.tx",
            self.Columns.T01_X: "CM.Traffic.T01.tx",
            self.Columns.T02_X: "CM.Traffic.T02.tx",
            self.Columns.CAR_TX: "CM.Car.tx",
            self.Columns.CAR_TY: "CM.Car.ty",
            self.Columns.NUMBER_OF_DYNAMIC_OBJS: "MTS.MTA_ADC5.SI_DATA.m_environmentModelPort.numberOfDynamicObjects_u8",
        }

        detected_dynamic_obj_x = {
            self.Columns.DYNAMIC_OBJ_X.format(
                f"{gen_id[0]}_{gen_id[1]}"
            ): f"MTS.MTA_ADC5.SI_DATA.m_environmentModelPort.dynamicObjects[{gen_id[0]}].objShape_m.array[{gen_id[1]}].x_dir"
            for gen_id in list(itertools.product(*signal_ids))
        }
        detected_dynamic_obj_y = {
            self.Columns.DYNAMIC_OBJ_Y.format(
                f"{gen_id[0]}_{gen_id[1]}"
            ): f"MTS.MTA_ADC5.SI_DATA.m_environmentModelPort.dynamicObjects[{gen_id[0]}].objShape_m.array[{gen_id[1]}].y_dir"
            for gen_id in list(itertools.product(*signal_ids))
        }
        detected_shape_act_size = {
            self.Columns.DYNAMIC_OBJ_SHAPE_ACT_SIZE.format(
                f"{gen_ig}"
            ): f"MTS.MTA_ADC5.SI_DATA.m_environmentModelPort.dynamicObjects[{gen_ig}].objShape_m.actualSize"
            for gen_ig in range(0, 4)
        }

        self._properties.update(detected_dynamic_obj_x)
        self._properties.update(detected_dynamic_obj_y)
        self._properties.update(detected_shape_act_size)


example_obj = ValidationSignals()


@teststep_definition(
    name="Detect and track test step",
    description="Check system capability to detect and continously track a traffic participant within the Traffic Participant detection zone",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, ValidationSignals)
class SotifDetectAndTrackCheck(TestStep):
    """SotifDetectAndTrackCheck Test Step."""

    custom_report = MfHilClCustomTeststepReport

    def __init__(self):
        """Init test."""
        super().__init__()

    @fh.HilClFuntions.log_exceptions
    def process(self, **kwargs):
        """
        This function processes the recorded signal from measurement file, set the result of the test,
        generate plots and additional results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        read_data = self.readers[SIGNAL_DATA]
        test_result = fc.INPUT_MISSING  # Result
        # plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_name = example_obj._properties
        test_result = fc.FAIL

        """Prepare sinals and variables"""
        signal_summary = {}
        time_signal = read_data.index
        t00_x_sig = read_data["t00_x"].tolist()
        t01_x_sig = read_data["t01_x"].tolist()
        t02_x_sig = read_data["t02_x"].tolist()
        car_tx_sig = read_data["Car_tx"].tolist()
        car_ty_sig = read_data["Car_ty"].tolist()

        evaluation1 = ""

        """Evaluation part"""
        dyn_obj_x_sig_list = []
        dyn_obj_y_sig_list = []
        shape_size_sig_list = []

        t_00_in_range_idx = []
        t_01_in_range_idx = []
        t_02_in_range_idx = []
        z0_shall_used = False
        z1_shall_used = False
        z2_shall_used = False

        z0_used = False
        z1_used = False
        z2_used = False

        beginig_of_checked_part = None
        end_of_checked_part = None

        number_of_all_traffic_participant = 20

        accapted_delay = 600  # ~ 600 ms

        local_drop_limit = (20 / 100) * constants.HilCl.SotifParameters.P_DROP

        limmit_market = [58] * len(time_signal)

        # Collect x and y realted signals
        for ids in list(itertools.product(*signal_ids)):
            column = ValidationSignals.Columns.DYNAMIC_OBJ_X.format(f"{ids[0]}_{ids[1]}")
            dyn_obj_x_sig_list.append(column)
            column = ValidationSignals.Columns.DYNAMIC_OBJ_Y.format(f"{ids[0]}_{ids[1]}")
            dyn_obj_y_sig_list.append(column)

        # Collect objShape_m.actualSize signals
        for cnt in range(0, 4):
            column = ValidationSignals.Columns.DYNAMIC_OBJ_SHAPE_ACT_SIZE.format(f"{cnt}")
            shape_size_sig_list.append(column)

        # Collect intervals when TP was in range
        delay_tag = False
        first_idx = None

        for counter in range(0, len(t00_x_sig)):
            if t00_x_sig[counter] < 58 and delay_tag is False:
                delay_tag = True
                first_idx = counter
            if delay_tag and counter > first_idx + accapted_delay:
                t_00_in_range_idx.append(counter)

        delay_tag = False
        first_idx = None

        for counter in range(0, len(t01_x_sig)):
            if t01_x_sig[counter] < 58 and delay_tag is False:
                delay_tag = True
                first_idx = counter
            if delay_tag and counter > first_idx + accapted_delay:
                t_01_in_range_idx.append(counter)

        delay_tag = False
        first_idx = None

        for counter in range(0, len(t02_x_sig)):
            if t02_x_sig[counter] < 58 and delay_tag is False:
                delay_tag = True
                first_idx = counter
            if delay_tag and counter > first_idx + accapted_delay:
                t_02_in_range_idx.append(counter)

        # Calculate begining and end of important period of measurement
        beginig_of_checked_part = min(min(t_00_in_range_idx), min(t_01_in_range_idx), min(t_02_in_range_idx))
        end_of_checked_part = max(max(t_00_in_range_idx), max(t_01_in_range_idx), max(t_02_in_range_idx))

        for cnt in range(beginig_of_checked_part, end_of_checked_part):
            # Check how many zones shall be used
            if cnt in t_00_in_range_idx:
                z0_shall_used = True
            if cnt in t_01_in_range_idx:
                z1_shall_used = True
            if cnt in t_02_in_range_idx:
                z2_shall_used = True

            # Create zones
            zone_0 = Polygon(
                [
                    (car_tx_sig[cnt] + 1, car_ty_sig[cnt]),
                    (car_tx_sig[cnt] + 1, car_ty_sig[cnt] + 5),
                    (car_tx_sig[cnt] + 10, car_ty_sig[cnt] + 5),
                    (car_tx_sig[cnt] + 10, car_ty_sig[cnt]),
                ]
            )
            zone_1 = Polygon(
                [
                    (car_tx_sig[cnt] + 1, car_ty_sig[cnt]),
                    (car_tx_sig[cnt] + 1, car_ty_sig[cnt] - 5),
                    (car_tx_sig[cnt] + 10, car_ty_sig[cnt] - 5),
                    (car_tx_sig[cnt] + 10, car_ty_sig[cnt]),
                ]
            )
            zone_2 = Polygon(
                [
                    (car_tx_sig[cnt], car_ty_sig[cnt] - 5),
                    (car_tx_sig[cnt], car_ty_sig[cnt] + 5),
                    (car_tx_sig[cnt] - 10, car_ty_sig[cnt] + 5),
                    (car_tx_sig[cnt] - 10, car_ty_sig[cnt] - 5),
                ]
            )

            z0_used = False
            z1_used = False
            z2_used = False

            # Detection related signal processing
            for ids in list(itertools.product(*signal_ids)):

                # Get name of actual columns
                column_x = ValidationSignals.Columns.DYNAMIC_OBJ_X.format(f"{ids[0]}_{ids[1]}")
                column_y = ValidationSignals.Columns.DYNAMIC_OBJ_Y.format(f"{ids[0]}_{ids[1]}")

                # Create signals from actuacl columns
                act_signal_x = read_data[column_x].tolist()
                act_signal_y = read_data[column_y].tolist()

                # Create a point what presents of detected point of traffic participant
                act_point = Point(act_signal_x[cnt], act_signal_y[cnt])

                # Check point is one of zone.
                if zone_0.contains(act_point):
                    z0_used = True
                    continue

                if zone_1.contains(act_point):
                    z1_used = True
                    continue

                if zone_2.contains(act_point):
                    z2_used = True
                    continue

            # Compare usage of zone with required usage
            if z0_shall_used and z0_used is False:
                number_of_all_traffic_participant -= 1

            if z1_shall_used and z1_used is False:
                number_of_all_traffic_participant -= 1

            if z2_shall_used and z2_used is False:
                number_of_all_traffic_participant -= 1

            if number_of_all_traffic_participant < local_drop_limit:
                test_result = fc.FAIL
                evaluation1 = " ".join(
                    f" Test FAILED. System was not capable to detect and track traffic partitipants with"
                    f" {local_drop_limit} at {time_signal[cnt]} us.".split()
                )
                break

        if number_of_all_traffic_participant >= local_drop_limit:
            test_result = fc.PASS
            evaluation1 = " ".join(
                f"Test PASSED. System was capable to detect and track traffic partitipants with"
                f" {local_drop_limit} during whole testun.".split()
            )

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE

        signal_summary["Detect and track TPs"] = evaluation1

        self.sig_sum = HilClFuntions.hil_convert_dict_to_pandas(signal_summary)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        """Generate chart if test result FAILED """

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time_signal, y=t00_x_sig, mode="lines", name=signal_name["t00_x"]))
        fig.add_trace(go.Scatter(x=time_signal, y=t01_x_sig, mode="lines", name=signal_name["t01_x"]))
        fig.add_trace(go.Scatter(x=time_signal, y=t02_x_sig, mode="lines", name=signal_name["t02_x"]))
        fig.add_trace(go.Scatter(x=time_signal, y=limmit_market, mode="lines", name="Limit marker for TPs"))

        for i in range(0, len(shape_size_sig_list)):
            act_sig = read_data[shape_size_sig_list[i]].tolist()
            fig.add_trace(
                go.Scatter(
                    x=time_signal,
                    y=act_sig,
                    mode="lines",
                    name=example_obj._properties[ValidationSignals.Columns.DYNAMIC_OBJ_SHAPE_ACT_SIZE.format(i)],
                )
            )

        fig.layout = go.Layout(yaxis=dict(tickformat="1"), xaxis=dict(tickformat="1"), xaxis_title="Time [us]")
        fig.update_layout(PlotlyTemplate.lgt_tmplt)

        plot_titles.append("")
        plots.append(fig)
        remarks.append("")

        """Calculate parameters to additional table"""

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
        }

        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = additional_results_dict


@testcase_definition(
    name="Detect and track a traffic participant within the Traffic Participant detection zone",
    description="The system shall detect and track a traffic participant within"
    f" the Traffic Participant detection zone with at least [Pdrop] ({constants.HilCl.SotifParameters.P_DROP} %)",
)
class SotifDetectAndTrack(TestCase):
    """SotifDetectAndTrack Test Case."""

    custom_report = MfHilClCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SotifDetectAndTrackCheck,
        ]
