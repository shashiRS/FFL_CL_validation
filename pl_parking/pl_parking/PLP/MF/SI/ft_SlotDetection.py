"""Slot detection functional test"""

import os
import sys

from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)

import math

import plotly.graph_objects as go

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, MfSignals
from pl_parking.PLP.MF.constants import ConstantsSlotDetection, GeneralConstants, PlotlyTemplate

SIGNAL_DATA = "MF_SLOTDETECTION"

example_obj = MfSignals()


@teststep_definition(
    step_number=1,
    name="Slot Detection",
    description=(
        "Slot Detection Time KPI for SIL. Check if the ParkingBoxPort contains slot for the respective moment of time."
    ),
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, MfSignals)
class TestStepFtParkingSlotDetection(TestStep):
    """Test step class"""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize test step."""
        super().__init__()

    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """
        try:
            self.result.details.update(
                {
                    "Plots": [],
                    "Plot_titles": [],
                    "Remarks": [],
                    "file_name": os.path.basename(self.artifacts[0].file_path),
                }
            )
            read_data = self.readers[SIGNAL_DATA].signals
            test_result = fc.INPUT_MISSING  # Result
            # plots and remarks need to have the same length
            plot_titles, plots, remarks = fh.rep([], 3)
            trigger_text = ""
            signal_summary = {}
            evaluation1 = None
            evaluation2 = None
            T2_INDEX = None
            signal_name = example_obj._properties
            number_of_parking_boxes = 0
            number_of_valid_parking_boxes = read_data["numValidParkingBoxes_nu"].tolist()
            parking_boxes_0 = read_data["parkingBox0"].tolist()
            furthestObject_sRoad = read_data["furthestObject_sRoad"].tolist()
            furthestObject_yaw = read_data["furthestObject_yaw"].tolist()
            odo_road = read_data["OdoRoad"].tolist()
            ap_time = read_data["time"].tolist()
            sceneInterpretationActive_nu = read_data["sceneInterpretationActive_nu"].tolist()
            parkingBoxesCoordinates = {}
            for i_parkingBox in range(ConstantsSlotDetection.EXPORTED_SLOTS_NUMBER):
                parkingBoxesCoordinates[i_parkingBox] = {}
                for i_vertex in range(ConstantsSlotDetection.EXPORTED_SLOT_VERTICES_NUMBER):
                    parkingBoxesCoordinates[i_parkingBox][i_vertex] = {}
                    parkingBoxesCoordinates[i_parkingBox][i_vertex]["x"] = read_data[
                        f"parkingBox{i_parkingBox}_slotCoordinates{i_vertex}_x"
                    ].tolist()
                    parkingBoxesCoordinates[i_parkingBox][i_vertex]["y"] = read_data[
                        f"parkingBox{i_parkingBox}_slotCoordinates{i_vertex}_y"
                    ].tolist()

            if not any(isSIActive == 1 for isSIActive in sceneInterpretationActive_nu):
                test_result = fc.NOT_ASSESSED
                evaluation1 = evaluation2 = "Evaluation skipped, because sceneInterpretationActive_nu=0"
                trigger_text = evaluation2
            else:
                sec_on_index_step = round(ap_time[2] - ap_time[1], 10)
                time_delay_index = int(round(ConstantsSlotDetection.TIME_DELAY / sec_on_index_step))
                if furthestObject_yaw[-1] > math.pi / 2:
                    furthestObjectAngleCompensation = (
                        math.cos(furthestObject_yaw[-1]) * ConstantsSlotDetection.CAR_LENGTH
                    )
                else:
                    furthestObjectAngleCompensation = 0
                egoFrontRoad = [
                    value + (ConstantsSlotDetection.CAR_LENGTH - ConstantsSlotDetection.CAR_OVERHANG)
                    for value in odo_road
                ]
                isEgoFrontShortBeforeFurthestObject = [
                    egoFrontRoad[i] > (furthestObject_sRoad[i] + furthestObjectAngleCompensation)
                    and (furthestObject_sRoad[i] != ConstantsSlotDetection.NO_ROAD_VALUE)
                    for i in range(len(odo_road))
                ]
                if any(isEgoFrontShortBeforeFurthestObject):
                    T2_INDEX = isEgoFrontShortBeforeFurthestObject.index(True) + time_delay_index

                if T2_INDEX is not None:
                    if T2_INDEX < len(number_of_valid_parking_boxes):
                        cond_1 = number_of_valid_parking_boxes[T2_INDEX] >= ConstantsSlotDetection.TRUE_VALUE
                        if cond_1:
                            evaluation1 = " ".join(
                                f"The evaluation for {signal_name['numValidParkingBoxes_nu']}                          "
                                "                   is PASSED,                                             a slot was"
                                " detected for the specific time instance:                                            "
                                f" {round(ap_time[T2_INDEX], 3)} s.".split()
                            )
                        else:
                            evaluation1 = " ".join(
                                f"The evaluation for {signal_name['numValidParkingBoxes_nu']}                          "
                                "                   is FAILED,                                             with the"
                                f" value < {ConstantsSlotDetection.TRUE_VALUE} at timestamp:                           "
                                f"                  {round(ap_time[T2_INDEX], 3)} s.".split()
                            )
                        number_of_parking_boxes = number_of_valid_parking_boxes[T2_INDEX]
                        cond_2 = False
                        for i_parkingBox in range(ConstantsSlotDetection.EXPORTED_SLOTS_NUMBER):
                            for i_vertex in range(ConstantsSlotDetection.EXPORTED_SLOT_VERTICES_NUMBER):
                                parkingBoxVertex_x = parkingBoxesCoordinates[i_parkingBox][i_vertex]["x"]
                                parkingBoxVertexToMarker = abs(
                                    parkingBoxVertex_x[T2_INDEX] - furthestObject_sRoad[T2_INDEX]
                                )
                                if parkingBoxVertexToMarker < ConstantsSlotDetection.MARKER_TO_SLOT_VERTEX_MAX_DIST:
                                    cond_2 = True
                                    break
                        if cond_2:
                            evaluation2 = " ".join(
                                "The evaluation for the slot position is PASSED,                                      "
                                "           a slot was detected for the specific time instance:                       "
                                f"                          {round(ap_time[T2_INDEX], 3)} s.".split()
                            )
                        else:
                            evaluation2 = " ".join(
                                "The evaluation for the slot position is FAILED,                                      "
                                "       because none of the slot vertices has sRoad coordinate ~                      "
                                f"                       {furthestObject_sRoad[T2_INDEX]}".split()
                            )

                        if cond_1 and cond_2:
                            test_result = fc.PASS
                            trigger_text = "Found"
                        else:
                            test_result = fc.FAIL
                            trigger_text = "Found"
                    else:
                        test_result = fc.FAIL
                        evaluation1 = evaluation2 = (
                            "Evaluation not possible, trigger value is greater than                            "
                            f" {len(number_of_valid_parking_boxes)} (out of range)."
                        )
                        trigger_text = evaluation1
                else:
                    test_result = fc.FAIL
                    evaluation1 = evaluation2 = "Evaluation not possible, trigger T2_INDEX was not found."
                    trigger_text = evaluation1

            signal_summary[signal_name["numValidParkingBoxes_nu"]] = evaluation1
            signal_summary[signal_name["parkingBox0"]] = evaluation2

            for i_parkingBox in range(ConstantsSlotDetection.EXPORTED_SLOTS_NUMBER):
                for i_vertex in range(ConstantsSlotDetection.EXPORTED_SLOT_VERTICES_NUMBER):
                    signal_summary[signal_name[f"parkingBox{i_parkingBox}_slotCoordinates{i_vertex}_x"]] = evaluation2
                    signal_summary[signal_name[f"parkingBox{i_parkingBox}_slotCoordinates{i_vertex}_y"]] = evaluation2

            self.sig_sum = fh.convert_dict_to_pandas(signal_summary)
            plot_titles.append("")
            plots.append(self.sig_sum)
            remarks.append("")

            if test_result == fc.PASS:
                self.result.measured_result = TRUE
            elif test_result == fc.NOT_ASSESSED:
                self.result.measured_result = DATA_NOK
            else:
                self.result.measured_result = FALSE

            if self.result.measured_result in [FALSE, DATA_NOK] or bool(GeneralConstants.ACTIVATE_PLOTS):
                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        x=ap_time,
                        y=number_of_valid_parking_boxes,
                        mode="lines",
                        name=signal_name["numValidParkingBoxes_nu"],
                    )
                )
                fig.add_trace(go.Scatter(x=ap_time, y=parking_boxes_0, mode="lines", name=signal_name["parkingBox0"]))
                fig.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
                fig.update_layout(PlotlyTemplate.lgt_tmplt)
                fig.add_annotation(
                    dict(
                        font=dict(color="black", size=12),
                        x=0,
                        y=-0.12,
                        showarrow=False,
                        text="Valid Parking Boxes",
                        textangle=0,
                        xanchor="left",
                        xref="paper",
                        yref="paper",
                    )
                )
                plot_titles.append("")
                plots.append(fig)
                remarks.append("")

                fig2 = go.Figure()
                fig2.add_trace(
                    go.Scatter(
                        x=ap_time, y=furthestObject_sRoad, mode="lines", name=signal_name["furthestObject_sRoad"]
                    )
                )
                fig2.add_trace(go.Scatter(x=ap_time, y=odo_road, mode="lines", name=signal_name["OdoRoad"]))
                for i_parkingBox in range(ConstantsSlotDetection.EXPORTED_SLOTS_NUMBER):
                    for i_vertex in range(ConstantsSlotDetection.EXPORTED_SLOT_VERTICES_NUMBER):
                        fig2.add_trace(
                            go.Scatter(
                                x=ap_time,
                                y=parkingBoxesCoordinates[i_parkingBox][i_vertex]["x"],
                                mode="lines",
                                name=f"parkingBox{i_parkingBox}_slotCoordinates{i_vertex}_x",
                            )
                        )
                fig2.layout = go.Layout(yaxis=dict(tickformat="20"), xaxis=dict(tickformat="20"), xaxis_title="Time[s]")
                fig2.update_layout(PlotlyTemplate.lgt_tmplt)
                fig2.add_annotation(
                    dict(
                        font=dict(color="black", size=12),
                        x=0,
                        y=-0.12,
                        showarrow=False,
                        text="Furthest object (slot marker) sRoad and slot coordinates",
                        textangle=0,
                        xanchor="left",
                        xref="paper",
                        yref="paper",
                    )
                )
                plot_titles.append(" ")
                plots.append(fig2)
                remarks.append("")

            """Add the data in the table from Functional Test Filter Results"""
            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
                "NrOfPB[TBD]": {
                    "value": number_of_parking_boxes,
                    "color": fh.apply_color(number_of_parking_boxes, 1, "=="),
                },
                "Trigger": {
                    "value": trigger_text,
                    "color": (fh.get_color(test_result)),
                },
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
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@testcase_definition(
    name="MF SLOT DETECTION",
    description=(
        "Slot Detection Time KPI for SIL. Check if the ParkingBoxPort contains slot for the respective moment of time."
    ),
)
class FtParkingSlotDetection(TestCase):
    """SlotDetection test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test step."""
        return [TestStepFtParkingSlotDetection]
