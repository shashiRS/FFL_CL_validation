"""Validation of test case SWKPI_CNC_OFC_Density."""

import logging
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
)

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CV.OFC.ft_helper import OFCSignals, decode_flows

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TSF_BASE = os.path.abspath(os.path.join(__file__, "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)

SIGNAL_DATA = "OFC_DENSITY"

NUM_AOI = 10 * 10

DENSITY_THRESHOLD = 10


@teststep_definition(
    step_number=1,
    name="OFC Density",
    description="For each timestamp calculate density and check if it is >= 10%.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, OFCSignals)
class OfcDensityTestStep(TestStep):
    """Test step definition."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()
        self.sig_sum = None

    def process(self):
        """Process the simulated file."""
        _log.debug("Starting processing...")

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        test_result = fc.INPUT_MISSING  # Result
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}

        # extract all signals into a dataframe
        reader_data = self.readers[SIGNAL_DATA]
        reader_data = reader_data.reset_index(drop=True)

        reader_data.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in reader_data.columns]

        fc_ts_status = np.array([])
        fc_fw_all_densities = np.array([])
        fc_bw_all_densities = np.array([])
        fc_first_ts_failed = 0

        lsc_ts_status = np.array([])
        lsc_fw_all_densities = np.array([])
        lsc_bw_all_densities = np.array([])
        lsc_first_ts_failed = 0

        rc_ts_status = np.array([])
        rc_fw_all_densities = np.array([])
        rc_bw_all_densities = np.array([])
        rc_first_ts_failed = 0

        rsc_ts_status = np.array([])
        rsc_fw_all_densities = np.array([])
        rsc_bw_all_densities = np.array([])
        rsc_first_ts_failed = 0

        fc_fw_flows_df = reader_data.filter(like=OFCSignals.Columns.FLOWMAPDATA_FORWARD_FRONT)
        fc_bw_flows_df = reader_data.filter(like=OFCSignals.Columns.FLOWMAPDATA_BACKWARD_FRONT)
        fc_fw_flows_df_np = fc_fw_flows_df.to_numpy()
        fc_bw_flows_df_np = fc_bw_flows_df.to_numpy()

        lsc_fw_flows_df = reader_data.filter(like=OFCSignals.Columns.FLOWMAPDATA_FORWARD_LEFT)
        lsc_bw_flows_df = reader_data.filter(like=OFCSignals.Columns.FLOWMAPDATA_BACKWARD_LEFT)
        lsc_fw_flows_df_np = lsc_fw_flows_df.to_numpy()
        lsc_bw_flows_df_np = lsc_bw_flows_df.to_numpy()

        rc_fw_flows_df = reader_data.filter(like=OFCSignals.Columns.FLOWMAPDATA_FORWARD_REAR)
        rc_bw_flows_df = reader_data.filter(like=OFCSignals.Columns.FLOWMAPDATA_BACKWARD_REAR)
        rc_fw_flows_df_np = rc_fw_flows_df.to_numpy()
        rc_bw_flows_df_np = rc_bw_flows_df.to_numpy()

        rsc_fw_flows_df = reader_data.filter(like=OFCSignals.Columns.FLOWMAPDATA_FORWARD_RIGHT)
        rsc_bw_flows_df = reader_data.filter(like=OFCSignals.Columns.FLOWMAPDATA_BACKWARD_RIGHT)
        rsc_fw_flows_df_np = rsc_fw_flows_df.to_numpy()
        rsc_bw_flows_df_np = rsc_bw_flows_df.to_numpy()

        image_height = reader_data[OFCSignals.Columns.IMAGE_HEIGHT][0]
        image_width = reader_data[OFCSignals.Columns.IMAGE_WIDTH][0]
        aoi_height = int(0.1 * image_height)
        aoi_width = int(0.1 * image_width)
        num_aoi_flows = aoi_height * aoi_width

        for idx_ts in reader_data.index:

            fc_fw_flow_map_data = fc_fw_flows_df_np[idx_ts]
            fc_bw_flow_map_data = fc_bw_flows_df_np[idx_ts]

            lsc_fw_flow_map_data = lsc_fw_flows_df_np[idx_ts]
            lsc_bw_flow_map_data = lsc_bw_flows_df_np[idx_ts]

            rc_fw_flow_map_data = rc_fw_flows_df_np[idx_ts]
            rc_bw_flow_map_data = rc_bw_flows_df_np[idx_ts]

            rsc_fw_flow_map_data = rsc_fw_flows_df_np[idx_ts]
            rsc_bw_flow_map_data = rsc_bw_flows_df_np[idx_ts]

            # decode the flow map data signal to obtain the motion vectors of the flows and their confidence score, for each camera
            fc_fw_of_vectors = decode_flows(
                image_height,
                image_width,
                fc_fw_flow_map_data,
                reader_data[OFCSignals.Columns.FLOWMAPDATAOFFSET_FORWARD_FRONT][idx_ts],
            )
            fc_bw_of_vectors = decode_flows(
                image_height,
                image_width,
                fc_bw_flow_map_data,
                reader_data[OFCSignals.Columns.FLOWMAPDATAOFFSET_BACKWARD_FRONT][idx_ts],
            )

            lsc_fw_of_vectors = decode_flows(
                image_height,
                image_width,
                lsc_fw_flow_map_data,
                reader_data[OFCSignals.Columns.FLOWMAPDATAOFFSET_FORWARD_LEFT][idx_ts],
            )
            lsc_bw_of_vectors = decode_flows(
                image_height,
                image_width,
                lsc_bw_flow_map_data,
                reader_data[OFCSignals.Columns.FLOWMAPDATAOFFSET_BACKWARD_LEFT][idx_ts],
            )

            rc_fw_of_vectors = decode_flows(
                image_height,
                image_width,
                rc_fw_flow_map_data,
                reader_data[OFCSignals.Columns.FLOWMAPDATAOFFSET_FORWARD_REAR][idx_ts],
            )
            rc_bw_of_vectors = decode_flows(
                image_height,
                image_width,
                rc_bw_flow_map_data,
                reader_data[OFCSignals.Columns.FLOWMAPDATAOFFSET_BACKWARD_REAR][idx_ts],
            )

            rsc_fw_of_vectors = decode_flows(
                image_height,
                image_width,
                rsc_fw_flow_map_data,
                reader_data[OFCSignals.Columns.FLOWMAPDATAOFFSET_FORWARD_RIGHT][idx_ts],
            )
            rsc_bw_of_vectors = decode_flows(
                image_height,
                image_width,
                rsc_bw_flow_map_data,
                reader_data[OFCSignals.Columns.FLOWMAPDATAOFFSET_BACKWARD_RIGHT][idx_ts],
            )

            fc_fw_sum_aoi_density = 0
            fc_bw_sum_aoi_density = 0

            lsc_fw_sum_aoi_density = 0
            lsc_bw_sum_aoi_density = 0

            rc_fw_sum_aoi_density = 0
            rc_bw_sum_aoi_density = 0

            rsc_fw_sum_aoi_density = 0
            rsc_bw_sum_aoi_density = 0

            for aoi_h in range(0, image_height - aoi_height, aoi_height):
                aoi_y_start = aoi_h
                aoi_y_final = int(aoi_h + aoi_height)
                for aoi_w in range(0, image_width - aoi_width, aoi_width):
                    aoi_x_start = aoi_w
                    aoi_x_final = int(aoi_w + aoi_width)

                    fc_fw_num_flows_aoi = 0
                    fc_bw_num_flows_aoi = 0

                    lsc_fw_num_flows_aoi = 0
                    lsc_bw_num_flows_aoi = 0

                    rc_fw_num_flows_aoi = 0
                    rc_bw_num_flows_aoi = 0

                    rsc_fw_num_flows_aoi = 0
                    rsc_bw_num_flows_aoi = 0

                    for row in range(aoi_x_start, aoi_x_final):
                        for col in range(aoi_y_start, aoi_y_final):
                            fc_fw_x_y = fc_fw_of_vectors[col][row][:2]
                            fc_fw_x_y_curr = [fc_fw_x_y[0] + col, fc_fw_x_y[1] + row]
                            if (
                                aoi_x_start <= fc_fw_x_y_curr[0] < aoi_x_final
                                and aoi_y_start <= fc_fw_x_y_curr[1] < aoi_y_final
                            ):
                                fc_fw_num_flows_aoi += 1
                            fc_bw_x_y = fc_bw_of_vectors[col][row][:2]
                            fc_bw_x_y_curr = [fc_bw_x_y[0] + col, fc_bw_x_y[1] + row]
                            if (
                                aoi_x_start <= fc_bw_x_y_curr[0] < aoi_x_final
                                and aoi_y_start <= fc_bw_x_y_curr[1] < aoi_y_final
                            ):
                                fc_bw_num_flows_aoi += 1

                            lsc_fw_x_y = lsc_fw_of_vectors[col][row][:2]
                            lsc_fw_x_y_curr = [lsc_fw_x_y[0] + col, lsc_fw_x_y[1] + row]
                            if (
                                aoi_x_start <= lsc_fw_x_y_curr[0] < aoi_x_final
                                and aoi_y_start <= lsc_fw_x_y_curr[1] < aoi_y_final
                            ):
                                lsc_fw_num_flows_aoi += 1
                            lsc_bw_x_y = lsc_bw_of_vectors[col][row][:2]
                            lsc_bw_x_y_curr = [lsc_bw_x_y[0] + col, lsc_bw_x_y[1] + row]
                            if (
                                aoi_x_start <= lsc_bw_x_y_curr[0] < aoi_x_final
                                and aoi_y_start <= lsc_bw_x_y_curr[1] < aoi_y_final
                            ):
                                lsc_bw_num_flows_aoi += 1

                            rc_fw_x_y = rc_fw_of_vectors[col][row][:2]
                            rc_fw_x_y_curr = [rc_fw_x_y[0] + col, rc_fw_x_y[1] + row]
                            if (
                                aoi_x_start <= rc_fw_x_y_curr[0] < aoi_x_final
                                and aoi_y_start <= rc_fw_x_y_curr[1] < aoi_y_final
                            ):
                                rc_fw_num_flows_aoi += 1
                            rc_bw_x_y = rc_bw_of_vectors[col][row][:2]
                            rc_bw_x_y_curr = [rc_bw_x_y[0] + col, rc_bw_x_y[1] + row]
                            if (
                                aoi_x_start <= rc_bw_x_y_curr[0] < aoi_x_final
                                and aoi_y_start <= rc_bw_x_y_curr[1] < aoi_y_final
                            ):
                                rc_bw_num_flows_aoi += 1

                            rsc_fw_x_y = rsc_fw_of_vectors[col][row][:2]
                            rsc_fw_x_y_curr = [rsc_fw_x_y[0] + col, rsc_fw_x_y[1] + row]
                            if (
                                aoi_x_start <= rsc_fw_x_y_curr[0] < aoi_x_final
                                and aoi_y_start <= rsc_fw_x_y_curr[1] < aoi_y_final
                            ):
                                rsc_fw_num_flows_aoi += 1
                            rsc_bw_x_y = rsc_bw_of_vectors[col][row][:2]
                            rsc_bw_x_y_curr = [rsc_bw_x_y[0] + col, rsc_bw_x_y[1] + row]
                            if (
                                aoi_x_start <= rsc_bw_x_y_curr[0] < aoi_x_final
                                and aoi_y_start <= rsc_bw_x_y_curr[1] < aoi_y_final
                            ):
                                rsc_bw_num_flows_aoi += 1
                    fc_fw_aoi_density = fc_fw_num_flows_aoi / num_aoi_flows * 100
                    fc_fw_sum_aoi_density = fc_fw_sum_aoi_density + fc_fw_aoi_density
                    fc_bw_aoi_density = fc_bw_num_flows_aoi / num_aoi_flows * 100
                    fc_bw_sum_aoi_density = fc_bw_sum_aoi_density + fc_bw_aoi_density

                    lsc_fw_aoi_density = lsc_fw_num_flows_aoi / num_aoi_flows * 100
                    lsc_fw_sum_aoi_density = lsc_fw_sum_aoi_density + lsc_fw_aoi_density
                    lsc_bw_aoi_density = lsc_bw_num_flows_aoi / num_aoi_flows * 100
                    lsc_bw_sum_aoi_density = lsc_bw_sum_aoi_density + lsc_bw_aoi_density

                    rc_fw_aoi_density = rc_fw_num_flows_aoi / num_aoi_flows * 100
                    rc_fw_sum_aoi_density = rc_fw_sum_aoi_density + rc_fw_aoi_density
                    rc_bw_aoi_density = rc_bw_num_flows_aoi / num_aoi_flows * 100
                    rc_bw_sum_aoi_density = rc_bw_sum_aoi_density + rc_bw_aoi_density

                    rsc_fw_aoi_density = rsc_fw_num_flows_aoi / num_aoi_flows * 100
                    rsc_fw_sum_aoi_density = rsc_fw_sum_aoi_density + rsc_fw_aoi_density
                    rsc_bw_aoi_density = rsc_bw_num_flows_aoi / num_aoi_flows * 100
                    rsc_bw_sum_aoi_density = rsc_bw_sum_aoi_density + rsc_bw_aoi_density

            fc_fw_density = round(fc_fw_sum_aoi_density / NUM_AOI, 2)
            fc_bw_density = round(fc_bw_sum_aoi_density / NUM_AOI, 2)
            fc_fw_all_densities = np.append(fc_fw_all_densities, fc_fw_density)
            fc_bw_all_densities = np.append(fc_bw_all_densities, fc_bw_density)

            lsc_fw_density = round(lsc_fw_sum_aoi_density / NUM_AOI, 2)
            lsc_bw_density = round(lsc_bw_sum_aoi_density / NUM_AOI, 2)
            lsc_fw_all_densities = np.append(lsc_fw_all_densities, lsc_fw_density)
            lsc_bw_all_densities = np.append(lsc_bw_all_densities, lsc_bw_density)

            rc_fw_density = round(rc_fw_sum_aoi_density / NUM_AOI, 2)
            rc_bw_density = round(rc_bw_sum_aoi_density / NUM_AOI, 2)
            rc_fw_all_densities = np.append(rc_fw_all_densities, rc_fw_density)
            rc_bw_all_densities = np.append(rc_bw_all_densities, rc_bw_density)

            rsc_fw_density = round(rsc_fw_sum_aoi_density / NUM_AOI, 2)
            rsc_bw_density = round(rsc_bw_sum_aoi_density / NUM_AOI, 2)
            rsc_fw_all_densities = np.append(rsc_fw_all_densities, rsc_fw_density)
            rsc_bw_all_densities = np.append(rsc_bw_all_densities, rsc_bw_density)

            if fc_fw_density >= DENSITY_THRESHOLD and fc_bw_density >= DENSITY_THRESHOLD:
                fc_ts_status = np.append(fc_ts_status, "passed")
            else:
                fc_ts_status = np.append(fc_ts_status, "failed")
                if fc_first_ts_failed == 0:
                    fc_first_ts_failed = reader_data["mts_ts"][idx_ts]

            if lsc_fw_density >= DENSITY_THRESHOLD and lsc_bw_density >= DENSITY_THRESHOLD:
                lsc_ts_status = np.append(lsc_ts_status, "passed")
            else:
                lsc_ts_status = np.append(lsc_ts_status, "failed")
                if lsc_first_ts_failed == 0:
                    lsc_first_ts_failed = reader_data["mts_ts"][idx_ts]

            if rc_fw_density >= DENSITY_THRESHOLD and rc_bw_density >= DENSITY_THRESHOLD:
                rc_ts_status = np.append(rc_ts_status, "passed")
            else:
                rc_ts_status = np.append(rc_ts_status, "failed")
                if rc_first_ts_failed == 0:
                    rc_first_ts_failed = reader_data["mts_ts"][idx_ts]

            if rsc_fw_density >= DENSITY_THRESHOLD and rsc_bw_density >= DENSITY_THRESHOLD:
                rsc_ts_status = np.append(rsc_ts_status, "passed")
            else:
                rsc_ts_status = np.append(rsc_ts_status, "failed")
                if rsc_first_ts_failed == 0:
                    rsc_first_ts_failed = reader_data["mts_ts"][idx_ts]

        fc_ts_check_all_passed = all(status == "passed" for status in fc_ts_status)
        lsc_ts_check_all_passed = all(status == "passed" for status in lsc_ts_status)
        rc_ts_check_all_passed = all(status == "passed" for status in rc_ts_status)
        rsc_ts_check_all_passed = all(status == "passed" for status in rsc_ts_status)

        if fc_ts_check_all_passed:
            fc_result = True
            fc_evaluation_message = f"The <b>evaluation</b> is <b>PASSED</b> for <b>FRONT CAMERA</b> because the density >= {DENSITY_THRESHOLD}%, for all timestamps."
        else:
            fc_result = False
            fc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>FRONT CAMERA</b> because for timestamp <b>{fc_first_ts_failed}</b> the density is < {DENSITY_THRESHOLD}%."

        if lsc_ts_check_all_passed:
            lsc_result = True
            lsc_evaluation_message = f"The <b>evaluation</b> is <b>PASSED</b> for <b>LEFT CAMERA</b> because the density >= {DENSITY_THRESHOLD}%, for all timestamps."
        else:
            lsc_result = False
            lsc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>LEFT CAMERA</b> because for timestamp <b>{lsc_first_ts_failed}</b> the density is < {DENSITY_THRESHOLD}%."

        if rc_ts_check_all_passed:
            rc_result = True
            rc_evaluation_message = f"The <b>evaluation</b> is <b>PASSED</b> for <b>REAR CAMERA</b> because the density >= {DENSITY_THRESHOLD}%, for all timestamps."
        else:
            rc_result = False
            rc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>REAR CAMERA</b> because for timestamp <b>{rc_first_ts_failed}</b> the density is < {DENSITY_THRESHOLD}%."

        if rsc_ts_check_all_passed:
            rsc_result = True
            rsc_evaluation_message = f"The <b>evaluation</b> is <b>PASSED</b> for <b>RIGHT CAMERA</b> because the density >= {DENSITY_THRESHOLD}%, for all timestamps."
        else:
            rsc_result = False
            rsc_evaluation_message = f"The <b>evaluation</b> is <b>FAILED</b> for <b>RIGHT CAMERA</b> because for timestamp <b>{rsc_first_ts_failed}</b> the density is < {DENSITY_THRESHOLD}%."

        cams_status_result = [
            fc_result,
            lsc_result,
            rc_result,
            rsc_result,
        ]
        test_result = fc.PASS if all(cams_status_result) else fc.FAIL

        signal_summary["FC_DENSITY"] = fc_evaluation_message
        signal_summary["LSC_DENSITY"] = lsc_evaluation_message
        signal_summary["RC_DENSITY"] = rc_evaluation_message
        signal_summary["RSC_DENSITY"] = rsc_evaluation_message

        remark = f"The percentage of density should be >= {DENSITY_THRESHOLD}%."

        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, table_remark=remark)
        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        fc_status = pd.DataFrame(
            {
                "Timestamp": np.array(reader_data["mts_ts"]),
                "Forward_density": fc_fw_all_densities,
                "Backward_density": fc_bw_all_densities,
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=fc_status["Timestamp"],
                y=fc_status["Forward_density"],
                marker={"color": "red"},
                name="Forward flows",
                hovertemplate="Timestamp: %{x}" + "<br>Forward flows density: %{y}%",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=fc_status["Timestamp"],
                y=fc_status["Backward_density"],
                marker={"color": "green"},
                name="Backward flows",
                hovertemplate="Timestamp: %{x}" + "<br>Backward flows density: %{y}%",
            )
        )
        fig["layout"]["yaxis"].update(title_text="Forward&Backward flows density percentages")
        fig["layout"]["xaxis"].update(title_text="Timestamps")
        fig.update_layout(hovermode="x unified")
        fig.update_traces(showlegend=True)

        remark = ""
        plot_titles.append("Front camera density percentages")
        plots.append(fig)
        remarks.append(remark)

        lsc_status = pd.DataFrame(
            {
                "Timestamp": np.array(reader_data["mts_ts"]),
                "Forward_density": lsc_fw_all_densities,
                "Backward_density": lsc_bw_all_densities,
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=lsc_status["Timestamp"],
                y=lsc_status["Forward_density"],
                marker={"color": "red"},
                name="Forward flows",
                hovertemplate="Timestamp: %{x}" + "<br>Forward flows density: %{y}%",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=lsc_status["Timestamp"],
                y=lsc_status["Backward_density"],
                marker={"color": "green"},
                name="Backward flows",
                hovertemplate="Timestamp: %{x}" + "<br>Backward flows density: %{y}%",
            )
        )
        fig["layout"]["yaxis"].update(title_text="Forward&Backward flows density percentages")
        fig["layout"]["xaxis"].update(title_text="Timestamps")
        fig.update_layout(hovermode="x unified")
        fig.update_traces(showlegend=True)

        remark = ""
        plot_titles.append("Left side camera density percentages")
        plots.append(fig)
        remarks.append(remark)

        rc_status = pd.DataFrame(
            {
                "Timestamp": np.array(reader_data["mts_ts"]),
                "Forward_density": rc_fw_all_densities,
                "Backward_density": rc_bw_all_densities,
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=rc_status["Timestamp"],
                y=rc_status["Forward_density"],
                marker={"color": "red"},
                name="Forward flows",
                hovertemplate="Timestamp: %{x}" + "<br>Forward flows density: %{y}%",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=rc_status["Timestamp"],
                y=rc_status["Backward_density"],
                marker={"color": "green"},
                name="Backward flows",
                hovertemplate="Timestamp: %{x}" + "<br>Backward flows density: %{y}%",
            )
        )
        fig["layout"]["yaxis"].update(title_text="Forward&Backward flows density percentages")
        fig["layout"]["xaxis"].update(title_text="Timestamps")
        fig.update_layout(hovermode="x unified")
        fig.update_traces(showlegend=True)

        remark = ""
        plot_titles.append("Rear camera density percentages")
        plots.append(fig)
        remarks.append(remark)

        rsc_status = pd.DataFrame(
            {
                "Timestamp": np.array(reader_data["mts_ts"]),
                "Forward_density": rsc_fw_all_densities,
                "Backward_density": rsc_bw_all_densities,
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=rsc_status["Timestamp"],
                y=rsc_status["Forward_density"],
                marker={"color": "red"},
                name="Forward flows",
                hovertemplate="Timestamp: %{x}" + "<br>Forward flows density: %{y}%",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=rsc_status["Timestamp"],
                y=rsc_status["Backward_density"],
                marker={"color": "green"},
                name="Backward flows",
                hovertemplate="Timestamp: %{x}" + "<br>Backward flows density: %{y}%",
            )
        )
        fig["layout"]["yaxis"].update(title_text="Forward&Backward flows density percentages")
        fig["layout"]["xaxis"].update(title_text="Timestamps")
        fig.update_layout(hovermode="x unified")
        fig.update_traces(showlegend=True)

        remark = ""
        plot_titles.append("Right side camera density percentages")
        plots.append(fig)
        remarks.append(remark)

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.FAIL:
            self.result.measured_result = FALSE
        else:
            self.result.measured_result = DATA_NOK

        for plot, plot_title, remark in zip(plots, plot_titles, remarks):
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(
                    f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                )
            else:
                self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")


@testcase_definition(
    name="SWKPI_CNC_OFC_Density",
    description="This test case calculates, for each timestamp, the density and checks if it is >= 10%.",
)
@register_inputs("/parking")
# @register_inputs("/TSF_DEBUG/")
class OfcDensity(TestCase):
    """Test case definition."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [OfcDensityTestStep]
