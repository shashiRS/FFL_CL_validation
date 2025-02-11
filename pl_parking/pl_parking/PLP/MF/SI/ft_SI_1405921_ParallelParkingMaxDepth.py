#!/usr/bin/env python3
"""The SceneInterpretation shall limit the maximum depth of a parallel parking box"""
# import libraries
import logging
import os
import sys
import tempfile
from pathlib import Path

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
    DATA_NOK,
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
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    SISignals,
    build_html_table,
    get_color,
)
from pl_parking.PLP.MF.constants import (
    ConstantsSI as threshold,
)
from pl_parking.PLP.MF.constants import (
    ConstantsTrajpla,
    PlotlyTemplate,
)
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""any test must have a specific and UNIQUE alias as it will contain a data frame
with all the signals for a test script"""
READER_NAME = "SI_ParallelParkingMaxDepth"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="Check for SI_ParallelParkingMaxDepth",
    description="The SceneInterpretation shall limit the maximum depth of a parallel parking box.",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_ParallelParkingMaxDepth(TestStep):
    """Example test step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {
                "Plots": [],
                "file_name": os.path.basename(self.artifacts[0].file_path),
            }
        )
        try:
            plots = []
            # Get the read data frame

            read_data = self.readers[READER_NAME]
            df = read_data.as_plain_df

            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
            ap_state = df[SISignals.Columns.AP_STATE]
            ap_time = df[SISignals.Columns.TIME].values.tolist()

            pb_signal_df = pd.DataFrame()
            sig_sum = {
                "Timestamp [s]": [],
                "Parallel PB width [m]": [],
                "MAX_DEPTH_PARALLEL_PARKING_BOX [m]": [],
                "description": [],
                "Result": [],
            }

            MAX_DEPTH_PARALLEL_PARKING_BOX_val_park = threshold.MAX_DEPTH_PARALLEL_PARKING_BOX_PARK
            MAX_DEPTH_PARALLEL_PARKING_BOX_val_Scan = threshold.MAX_DEPTH_PARALLEL_PARKING_BOX_SCAN

            pb_with_marker_match = {}
            table_remark = f"The SceneInterpretation shall limit the maximum depth of a parallel parking box to <br> {MAX_DEPTH_PARALLEL_PARKING_BOX_val_Scan} [m] during Scanning Mode  /or/ {MAX_DEPTH_PARALLEL_PARKING_BOX_val_park} [m] during Parking Mode  to the curb side edge. <br><br>"

            pb_count = len([x for x in list(df.columns) if SISignals.Columns.PB_SLOTCORDINATES_FRONTLEFT_X in x])
            # Combine all coordinates into a single list for each parking box
            for i in range(pb_count):
                pb_signal_df[SISignals.Columns.PARKBOX_COORDINATES_LIST.format(i)] = df[
                    [x.format(i) for x in ft_helper.combined_list_for_all_pb]
                ].apply(lambda row: row.values.tolist(), axis=1)

            pb_col_with_values = [
                col for col in pb_signal_df.columns if not pb_signal_df[col].apply(ft_helper.is_all_zeros).all()
            ]
            pb_signal_df = pb_signal_df[pb_col_with_values]
            num_valid_pb = df[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU]

            mask_apstate_park_scan_in = (ap_state == ConstantsTrajpla.AP_AVG_ACTIVE_IN) | (
                ap_state == ConstantsTrajpla.AP_SCAN_IN
            )

            mask_num_valid_pb = (
                num_valid_pb[mask_apstate_park_scan_in].rolling(2).apply(lambda x: x[0] < x[1], raw=True)
            )
            m_num_valid_pb = num_valid_pb != 0
            numValidPbTimestamps = [row for row, val in mask_num_valid_pb.items() if val == 1]

            # Combine masks to get the final mask with valid values
            mask_final = (
                pb_signal_df.applymap(lambda x: any(i != 0 for i in x)).any(axis=1)
                & mask_apstate_park_scan_in
                & m_num_valid_pb
            )
            # Apply mask to get the final dataframe

            pb_filtered_df = pb_signal_df[mask_final]

            # delim_col_with_values =[col for col in pb_filtered_df.columns if not pb_filtered_df[col].apply(ft_helper.is_all_zeros).all()]
            filtered_timestamps = list(pb_filtered_df.index)
            ap_time = [round(i, 3) for i in ap_time]

            # Create a dictionary to store the collected data
            collect_data_dict = {
                ts: {
                    "pb": {},
                    "ts": ap_time[list(df.index).index(ts)],
                    "ap_state": ap_state.loc[ts],
                    "markers": {},
                    "MAX_DEPTH_PARALLEL_PARKING_BOX": {},
                    "verdict": {},
                    "pb_width": {},
                    "description": {},
                }
                for ts in filtered_timestamps
            }

            # Transform apstate to list
            ap_state = ap_state.values.tolist()

            for timestamp_val in filtered_timestamps:
                pb_with_marker_match.clear()

                pb_from_ts = {x: [(0.0, 0.0)] * 4 for x in range(len(pb_col_with_values))}

                for i, col_name in enumerate(pb_col_with_values):
                    pb_coords = pb_signal_df[col_name].loc[timestamp_val]
                    vertices_pb = list(zip(pb_coords[::2], pb_coords[1::2]))
                    pb_from_ts[i] = vertices_pb
                # Remove the parking box with all zeros
                pb_from_ts = {x: y for x, y in pb_from_ts.items() if all(val1 != 0 for val1, val2 in y)}

                if pb_from_ts:

                    the_state_of_ap = collect_data_dict[timestamp_val]["ap_state"]

                    park_box_id = list(pb_from_ts.keys())[0]
                    vertices_pb = pb_from_ts[park_box_id]
                    distances_between_pb = ft_helper.quadrilateral_distances(vertices_pb)
                    AB_width_pb = float(f'{distances_between_pb.get("AB",0):.2f}')

                    collect_data_dict[timestamp_val]["pb_width"][park_box_id] = AB_width_pb

                    collect_data_dict[timestamp_val]["description"][
                        park_box_id
                    ] = f"The parallel parking box has a width of {AB_width_pb} [m], which must not exceed the maximum width of \
                    {MAX_DEPTH_PARALLEL_PARKING_BOX_val_park} [m].The validation occurs when the value from the {signals_obj._properties[SISignals.Columns.AP_STATE]} \
                    signal is set to {ft_helper.ap_state_dict(the_state_of_ap)}."

                    collect_data_dict[timestamp_val]["MAX_DEPTH_PARALLEL_PARKING_BOX"][
                        park_box_id
                    ] = MAX_DEPTH_PARALLEL_PARKING_BOX_val_park
                    collect_data_dict[timestamp_val]["verdict"][park_box_id] = (
                        "PASS" if MAX_DEPTH_PARALLEL_PARKING_BOX_val_park >= AB_width_pb else "FAIL"
                    )

            res = [val["verdict"][x] for val in collect_data_dict.values() for x in val["verdict"].keys()]
            if res and pb_from_ts:
                res = all([x == "PASS" for x in res])
                if res:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE
                    for ts in numValidPbTimestamps:

                        for pb_id in collect_data_dict[ts]["pb_width"].keys():
                            sig_sum["Timestamp [s]"].append(collect_data_dict[ts]["ts"])
                            sig_sum["Parallel PB width [m]"].append(collect_data_dict[ts]["pb_width"][pb_id])
                            sig_sum["MAX_DEPTH_PARALLEL_PARKING_BOX [m]"].append(
                                collect_data_dict[ts]["MAX_DEPTH_PARALLEL_PARKING_BOX"][pb_id]
                            )
                            sig_sum["description"].append(collect_data_dict[ts]["description"][pb_id])
                            sig_sum["Result"].append(
                                ft_helper.get_result_color(collect_data_dict[ts]["verdict"][pb_id])
                            )

                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    plots.append(sig_sum)

                else:
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE
                    for ts, val in collect_data_dict.items():
                        if ts:
                            for pb_id in val["pb_width"].keys():
                                if val["verdict"][pb_id] == "FAIL":
                                    sig_sum["Timestamp [s]"].append(val["ts"])
                                    sig_sum["Parallel PB width [m]"].append(val["pb_width"][pb_id])
                                    sig_sum["MAX_DEPTH_PARALLEL_PARKING_BOX [m]"].append(
                                        val["MAX_DEPTH_PARALLEL_PARKING_BOX"][pb_id]
                                    )
                                    sig_sum["description"].append(val["description"][pb_id])
                                    sig_sum["Result"].append(ft_helper.get_result_color(val["verdict"][pb_id]))

                    sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                    sig_sum = ft_helper.create_hidden_table(
                        sig_sum, 1, button_text="Show Table Parallel_Parking_Width information"
                    )
                    plots.append(sig_sum)

                signal_fig = go.Figure()
                signal_fig.add_trace(
                    go.Scatter(
                        x=ap_time,
                        y=ap_state,
                        mode="lines",
                        name=signals_obj._properties[SISignals.Columns.AP_STATE],
                        text=[
                            f"Timestamp: {ap_time[idx]} <br>" f"AP State: {ft_helper.ap_state_dict(state)}"
                            for idx, state in enumerate(ap_state)
                        ],
                        hoverinfo="text",
                    )
                )
                signal_fig.add_trace(
                    go.Scatter(
                        x=ap_time,
                        y=df[SISignals.Columns.NUMVALIDPARKINGBOXES_NU].values.tolist(),
                        mode="lines",
                        name=signals_obj._properties[SISignals.Columns.NUMVALIDPARKINGBOXES_NU][0],
                    )
                )

                signal_fig.layout = go.Layout(
                    yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time [s]"
                )
                signal_fig.update_layout(
                    PlotlyTemplate.lgt_tmplt,
                    title="AP State and Number of Valid Parking Boxes",
                )

                plots.append(signal_fig)
            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                sig_sum = ({"Evaluation not possible": "DATA_NOK"},)
                sig_sum = build_html_table(pd.DataFrame(sig_sum), table_remark=table_remark)
                plots.append(sig_sum)

            for plot in plots:
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
                else:
                    self.result.details["Plots"].append(plot)

            """Add the data in the table from Functional Test Filter Results"""
            additional_results_dict = {
                "Verdict": {"value": test_result.title(), "color": get_color(test_result)},
            }
            self.result.details["Additional_results"] = additional_results_dict
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("ReqId_1405921")
@testcase_definition(
    name="SI_ParallelParkingMaxDepthTC",
    description="The SceneInterpretation shall limit the maximum depth of a parallel parking box.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_9tyHpjpwEe6GONELpfdJ2Q&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F17099",
)
@register_inputs("/Playground_2/TSF-Debug")
class SI_ParallelParkingMaxDepthTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_ParallelParkingMaxDepth,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\1405921_and_1405923\SISim_UC_Parallel_Empty_Prk_Max_Depth.testrun.erg"

    debug(
        SI_ParallelParkingMaxDepthTC,
        # test_bsigs,
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
