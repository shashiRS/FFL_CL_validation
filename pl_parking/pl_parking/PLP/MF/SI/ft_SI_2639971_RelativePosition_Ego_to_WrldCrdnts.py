"""Ego Vehicle Relative Position Validation"""

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

import pl_parking.common_ft_helper as fh

"""imports from current repo"""
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import (
    MfCustomTeststepReport,
    SISignals,
    build_html_table,
    get_color,
)
from pl_parking.PLP.MF.SI import ft_helper

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SIGNAL_DATA = "SI_EgoVehicleRelativePositionValidation"
signals_obj = SISignals()


@teststep_definition(
    step_number=1,
    name="SI_EgoVehicleRelativePositionValidation",
    description="Verify Ego Vehicle Relative Position to the World Coordinate System.",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SISignals)
class SI_EgoVehicleRelativePositionValidation(TestStep):
    """Test Step for verifying ego vehicle position relative to world coordinate system."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the test step."""
        super().__init__()

    def process(self, **kwargs):
        """Evaluating test case."""
        _log.debug("Starting process for ego vehicle relative position validation...")
        self.result.details.update({"Plots": [], "file_name": os.path.basename(self.artifacts[0].file_path)})

        try:
            plots = []
            # Get the read data frame
            read_data = self.readers[SIGNAL_DATA]
            self.test_result = fc.INPUT_MISSING
            self.result.measured_result = DATA_NOK
            plot_titles, plots, remarks = fh.rep([], 3)

            # Extract columns for ego vehicle position
            df = read_data.as_plain_df
            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]
            df.columns = df.columns.str.replace(r"\\n", "", regex=True)
            ap_time = df[SISignals.Columns.TIME].values.tolist()
            ap_time = [round(i, 3) for i in ap_time]

            # Check for required columns
            if (
                "envModelPort.egoVehiclePoseForAP.pos_x_m" not in df.columns
                or "envModelPort.egoVehiclePoseForAP.pos_y_m" not in df.columns
                or "AP.odoEstimationPort.xPosition_m" not in df.columns
                or "AP.odoEstimationPort.yPosition_m" not in df.columns
            ):
                _log.error("Required signals for ego vehicle position are missing in the data.")
                self.result.measured_result = FALSE
                return
            # Filter data for timestamps >=0.32 seconds[detection will happen after 0.32s]
            filtered_data = df[df[SISignals.Columns.TIME] >= 0.33]
            if filtered_data.empty:
                _log.warning("No valid data points after the specified timestamp (0.33s).")
                self.result.measured_result = fc.NOT_ASSESSED
                table_data = pd.DataFrame({"Evaluation not possible": ["NO_VALID_DATA"]})
                sig_sum_html = build_html_table(table_data, table_remark="No valid data points after 0.33s.")
                self.result.details["Plots"].append(sig_sum_html)
                return

            # Extract the ego vehicle position data
            ego_x_values = filtered_data["envModelPort.egoVehiclePoseForAP.pos_x_m"].tolist()
            ego_y_values = filtered_data["envModelPort.egoVehiclePoseForAP.pos_y_m"].tolist()
            odo_x_values = filtered_data["AP.odoEstimationPort.xPosition_m"].tolist()
            odo_y_values = filtered_data["AP.odoEstimationPort.yPosition_m"].tolist()

            timestamps = filtered_data[SISignals.Columns.TIME].tolist()

            # Validate data and prepare result
            table_remark = (
                "<b>The SceneInterpretation shall provide the relative position of the ego vehicle "
                "to the world coordinate system in each frame.</b><br><br>"
            )

            # Result_List = [
            #     ft_helper.get_result_color("PASS") if d0  and d1  else ft_helper.get_result_color("FAIL")
            #     for d0,d1 in zip(ego_x_values,ego_y_values)
            # ]
            Result_list = [
                (
                    ft_helper.get_result_color("PASS")
                    if abs(ex - ox) <= 0.5 and abs(ey - oy) <= 0.5
                    else ft_helper.get_result_color("FAIL")
                )
                for ex, ey, ox, oy in zip(ego_x_values, ego_y_values, odo_x_values, odo_y_values)
            ]

            if ego_x_values and ego_y_values:

                if all(value == 0 for value in ego_x_values) and all(value == 0 for value in ego_y_values):
                    test_result = fc.FAIL
                    self.result.measured_result = FALSE

                    table_data = pd.DataFrame(
                        {
                            "Timestamp [s]": timestamps,
                            "Ego Position X [m]": ego_x_values,
                            "Ego Position Y [m]": ego_y_values,
                            "GT Position X [m]": odo_x_values,
                            "GT Position Y [m]": odo_y_values,
                            "Result": Result_list,
                        }
                    )

                    sig_sum_html = build_html_table(table_data, table_remark=table_remark)
                    sig_sum_html = ft_helper.create_hidden_table(
                        sig_sum_html, 1, button_text="Ego Vehicle Position Table"
                    )
                    self.result.details["Plots"].append(sig_sum_html)

                else:
                    test_result = fc.PASS
                    self.result.measured_result = TRUE

                    table_data = pd.DataFrame(
                        {
                            "Timestamp [s]": timestamps,
                            "Ego Position X [m]": ego_x_values,
                            "Ego Position Y [m]": ego_y_values,
                            "GT Position X [m]": odo_x_values,
                            "GT Position Y [m]": odo_y_values,
                            "Result": Result_list,
                        }
                    )

                    sig_sum_html = build_html_table(table_data, table_remark=table_remark)
                    sig_sum_html = ft_helper.create_hidden_table(
                        sig_sum_html, 1, button_text="Ego Vehicle Position Table"
                    )
                    self.result.details["Plots"].append(sig_sum_html)

                #####
                # Plot ego vehicle and ground truth positions over time
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=ego_x_values,
                        mode="lines+markers",
                        name="Ego Position X",
                        line=dict(color="blue"),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=ego_y_values,
                        mode="lines+markers",
                        name="Ego Position Y",
                        line=dict(color="green"),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=odo_x_values,
                        mode="lines+markers",
                        name="GT Position X",
                        line=dict(color="red", dash="dash"),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=odo_y_values,
                        mode="lines+markers",
                        name="GT Position Y",
                        line=dict(color="orange", dash="dash"),
                    )
                )
                fig.update_layout(
                    title="Ego Vehicle and GT Position Over Time",
                    xaxis_title="Timestamp (s)",
                    yaxis_title="Position (m)",
                    template="plotly_white",
                    font=dict(size=14),
                )

                plots.append(fig)

                ####

            else:
                test_result = fc.NOT_ASSESSED
                self.result.measured_result = DATA_NOK
                table_data = ({"Evaluation not possible": "DATA_NOK"},)
                table_data = build_html_table(pd.DataFrame(table_data), table_remark=table_remark)
                plots.append(table_data)

            #######
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

            #######


@verifies("ReqId_2639971")
@testcase_definition(
    name="SI_EgoVehicleRelativePositionValidation",
    description="Test Case for Ego Vehicle Relative Position Validation.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_Hk766W57Ee--TbjFlqqgJw&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
@register_inputs("/Playground_2/TSF-Debug")
class SI_EgoVehicleRelativePositionValidationTC(TestCase):
    """Test Case for verifying ego vehicle relative position to world coordinate system."""

    @property
    def test_steps(self):
        """Define the test steps."""
        return [SI_EgoVehicleRelativePositionValidation]


def main(data_folder, temp_dir=None, open_explorer=True):
    """Main entry point for debugging the test case."""
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\2639971_new\SISim_ParRight__sit4_vEgo20_DynObs.testrun 10.erg"
    debug(
        SI_EgoVehicleRelativePositionValidationTC,
        # test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
    )


if __name__ == "__main__":
    working_directory = Path(tempfile.mkdtemp("_tsf"))

    data_folder = working_directory / "data"
    out_folder = working_directory / "out"

    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)
