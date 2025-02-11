#!/usr/bin/env python3

"""req id : 1717086
Body-traversable objects that delimit the free spaces on the right or left side shall not allow parking with the
ego car's boot or front (bumper) overhanging them.
- Inputs to SI:
○ SgfOutput.staticObjectsOutput.staticObjectVerticesOutput.numberOfVertices
○ SgfOutput.staticObjectsOutput.staticObjectVerticesOutput.vertices[%]
○ SgfOutput.staticObjectsOutput.numberOfObjects
○ SgfOutput.staticObjectsOutput.objects[%].heightConfidences
- Outputs of SI:
○ ApParkingBoxPort.numValidParkingBoxes_nu
○ ApParkingBoxPort.parkingBoxes[%].slotCoordinates_m
"""

"""import libraries"""
import logging
import os
import sys

# import seaborn as sns
import pandas as pd
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import (
    FALSE,
    TRUE,
    BooleanResult,
)
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

"""imports from current repo"""

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    SISignals,
)
from pl_parking.PLP.MF.constants import PlotlyTemplate
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""any test must have a specific and UNIQUE alias as it will contain a data frame
with all the signals for a test script"""

READER_NAME = "SI_1405861"
signals_obj = SISignals()


@teststep_definition(
    name="Test slot opening consistency",
    description="The detected slot opening shall remain relatively constant for a constant environment.",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_Slot_Opening_Consistency_TS(TestStep):
    """Example test step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        try:
            pb_opening_left = [
                "pb_slotCoordinates_FrontLeftx_{}",
                "pb_slotCoordinates_FrontLefty_{}",
            ]
            pb_opening_right = [
                "pb_slotCoordinates_FrontRightx_{}",
                "pb_slotCoordinates_FrontRighty_{}",
            ]

            # Get the read data frame
            read_data = self.readers[READER_NAME]
            self.test_result = fc.INPUT_MISSING  # Result
            THRESHOLD = 0.001
            df = read_data.as_plain_df
            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

            # plots and remarks need to have the same length
            plots = []
            signal_summary = {}
            num_valid_parking_boxes = df[SISignals.Columns.NUMVALIDPARKINGBOXES_NU] != 0
            evaluation = [False] * 2
            opening_left = df[num_valid_parking_boxes][[x.format(0) for x in pb_opening_left]].apply(
                lambda row: row.values.tolist(), axis=1
            )
            opening_right = df[num_valid_parking_boxes][[x.format(0) for x in pb_opening_right]].apply(
                lambda row: row.values.tolist(), axis=1
            )

            x_left, y_left = opening_left.apply(lambda coords: coords[0]), opening_left.apply(lambda coords: coords[1])
            std_x1, std_y1 = x_left.std(), y_left.std()

            x_right, y_right = opening_right.apply(lambda coords: coords[0]), opening_right.apply(
                lambda coords: coords[1]
            )
            std_x2, std_y2 = x_right.std(), y_right.std()

            opening_left = df[[x.format(0) for x in pb_opening_left]].apply(lambda row: row.values.tolist(), axis=1)
            opening_right = df[[x.format(0) for x in pb_opening_right]].apply(lambda row: row.values.tolist(), axis=1)
            x_left, y_left = opening_left.apply(lambda coords: coords[0]), opening_left.apply(lambda coords: coords[1])
            x_right, y_right = opening_right.apply(lambda coords: coords[0]), opening_right.apply(
                lambda coords: coords[1]
            )

            if std_x1 < THRESHOLD and std_y1 < THRESHOLD:
                evaluation[0] = True
            if std_x2 < THRESHOLD and std_y2 < THRESHOLD:
                evaluation[1] = True
            if all(evaluation):
                self.test_result = fc.PASS
                self.result.measured_result = TRUE
            else:
                self.test_result = fc.FAIL
                self.result.measured_result = FALSE
            ap_time = round(df[SISignals.Columns.TIME], 2)
            if evaluation[0]:
                eval_string_left = "Coordinates of the detected slot opening on the left side are relatively constant."
            else:
                eval_string_left = f"Coordinates of the detected slot opening on the left side are not relatively constant, with a standard deviation of X: {std_x1:.3f} [m] and Y: {std_y1:.3f} [m]."
            if evaluation[1]:
                eval_string_right = (
                    "Coordinates of the detected slot opening on the right side are relatively constant."
                )
            else:
                eval_string_right = f"Coordinates of the detected slot opening on the right side are not relatively constant, with a standard deviation of X: {std_x2:.3f} [m] and Y: {std_y2:.3f} [m]."
            signal_summary = {
                "Slot Opening": {"0": "Left", "1": "Right"},
                "Evaluation": {"0": eval_string_left, "1": eval_string_right},
                "Result": {
                    "0": ft_helper.get_result_color(evaluation[0]),
                    "1": ft_helper.get_result_color(evaluation[1]),
                },
            }
            signal_fig = go.Figure()
            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=df[SISignals.Columns.NUMVALIDPARKINGBOXES_NU].values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[SISignals.Columns.NUMVALIDPARKINGBOXES_NU][0],
                    text=[
                        f"Timestamp: {ap_time.iloc[idx]} <br>" f"Valid PB:<br>" f"{state}"
                        for idx, state in enumerate(df[SISignals.Columns.NUMVALIDPARKINGBOXES_NU].values.tolist())
                    ],
                    hoverinfo="text",
                )
            )

            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=x_left,
                    mode="lines",
                    name=signals_obj._properties[SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X_0][0],
                    text=[
                        f"Timestamp: {ap_time.iloc[idx]} <br>" f"X coords for Left opening:<br>" f"{state}"
                        for idx, state in enumerate(x_left)
                    ],
                    hoverinfo="text",
                )
            )
            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=y_left,
                    mode="lines",
                    name=signals_obj._properties[SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_Y_0][0],
                    text=[
                        f"Timestamp: {ap_time.iloc[idx]} <br>" f"Y coords for Left opening:<br>" f"{state}"
                        for idx, state in enumerate(y_left)
                    ],
                    hoverinfo="text",
                )
            )
            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=x_right,
                    mode="lines",
                    name=signals_obj._properties[SISignals.Columns.PB_SLOTCORDINATES_FRONTRIGHT_X_0][0],
                    text=[
                        f"Timestamp: {ap_time.iloc[idx]} <br>" f"X coords for Right opening:<br>" f"{state}"
                        for idx, state in enumerate(x_right)
                    ],
                    hoverinfo="text",
                )
            )
            signal_fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=y_right,
                    mode="lines",
                    name=signals_obj._properties[SISignals.Columns.PB_SLOTCORDINATES_FRONTRIGHT_Y_0][0],
                    text=[
                        f"Timestamp: {ap_time.iloc[idx]} <br>" f"Y coords for Right opening:<br>" f"{state}"
                        for idx, state in enumerate(y_right)
                    ],
                    hoverinfo="text",
                )
            )

            signal_fig.layout = go.Layout(
                yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]"
            )
            signal_fig.update_layout(
                PlotlyTemplate.lgt_tmplt,
                title="AP State and Number of Valid Parking Boxes",
            )

            sig_sum = fh.build_html_table(pd.DataFrame(signal_summary))
            plots.append(sig_sum)
            plots.append(signal_fig)

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)

        except Exception as err:
            print(str(err))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("ReqId_1717086")
@testcase_definition(
    name="SI Slot opening consistency",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_bZ1VIIVBEe6zAbWzhfU4xA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36324",
    description="The detected slot opening shall remain relatively constant for a constant environment.",
)
@register_inputs("/parking")
class SI_Slot_Opening_Consistency_TC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_Slot_Opening_Consistency_TS,
        ]
