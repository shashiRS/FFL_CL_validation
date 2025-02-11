"""
In Maneuvering Mode, the SceneInterpretation shall provide
only the parking box which was selected by the driver for park in maneuver.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

# import seaborn as sns
import plotly.graph_objects as go

import pl_parking.common_ft_helper as fh

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
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
    SISignals,
)
from pl_parking.PLP.MF.constants import AUPConstants

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""any test must have a specific and UNIQUE alias as it will contain a data frame
with all the signals for a test script"""
READER_NAME = "SI_ParkInPersistence"
signals_obj = SISignals()


@teststep_definition(
    name="Check for SI_ParkingBoxVisibleParkIn",
    description="Checks if a valid parking box in consistently offered during the parking process.",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_ParkingBoxVisibleParkIn(TestStep):
    """Example test step."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        super().__init__()
        self.sig_sum = None

    def process(self, **kwargs):
        """Evaluating test case"""
        _log.debug("Starting processing...")
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        try:
            plot_titles, plots, remarks = fh.rep([], 3)
            signal_summary = {}
            self.fig = go.Figure()
            test_result = fc.FAIL
            read_data = self.readers[READER_NAME]

            df = read_data.as_plain_df
            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

            ap_state = df[SISignals.Columns.AP_STATE]
            ap_time = df[SISignals.Columns.TIME].values.tolist()
            ap_time = [round(i, 3) for i in ap_time]

            num_valid_pb = df[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU]
            ap_state = ap_state.values.tolist()

            start_idx_list = df.index[
                df[SISignals.Columns.AP_STATE] == AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN
            ].tolist()
            start_idx = start_idx_list[0] if start_idx_list else None

            evaluation1 = " ".join(
                f"The evaluation of {signals_obj._properties[SISignals.Columns.AP_STATE]} is FAILED, \
                    the value <b>AP_AVG_ACTIVE_IN({AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN})</b> was never found.".split()
            )

            evaluation2 = " ".join(
                f"The evaluation of {signals_obj._properties[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU][0]} could not \
                    be evaluated due to the absence of values \
                        <b>AP_AVG_ACTIVE_IN({AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN})</b> or \
                                {signals_obj._properties[SISignals.Columns.AP_STATE]}.".split()
            )

            if start_idx is not None:
                for timestamp_val in df.index[df.index >= start_idx]:
                    if num_valid_pb[timestamp_val] == 1:
                        test_result = fc.PASS
                        evaluation2 = " ".join(
                            f"The evaluation of {signals_obj._properties[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU][0]} is PASSED. \
                                A single parking box was visible during 'Maneuvering Mode'.".split()
                        )
                    else:
                        test_result = fc.FAIL
                        evaluation2 = " ".join(
                            f"The evaluation of {signals_obj._properties[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU][0]} is FAILED. \
                            A total of {num_valid_pb[timestamp_val]} slots were visible during 'Maneuvering Mode' -- at timestamp \
                            {round(df[SISignals.Columns.TIME][timestamp_val], 2)}s ({timestamp_val}).".split()
                        )
                        break
                evaluation1 = " ".join(
                    f"The evaluation of {signals_obj._properties[SISignals.Columns.AP_STATE]} is PASSED, \
                        the value of <b>AP_AVG_ACTIVE_IN({AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN})</b> was found at \
                            timestamp {round(df[SISignals.Columns.TIME][start_idx], 2)}s ({start_idx}).".split()
                )
            signal_summary[f"{signals_obj._properties[SISignals.Columns.AP_STATE]} - AP_AVG_ACTIVE_IN"] = evaluation1
            signal_summary[signals_obj._properties[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU][0]] = evaluation2

            if test_result == fc.PASS:
                self.result.measured_result = TRUE
            else:
                self.result.measured_result = FALSE

            plot_titles.append("Signals Evaluation")
            self.sig_sum = fh.convert_dict_to_pandas(signal_summary=signal_summary)
            plots.append(self.sig_sum)
            remarks.append("")

            self.fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=num_valid_pb.values.tolist(),
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU][0],
                )
            )
            self.fig.add_trace(
                go.Scatter(
                    x=ap_time,
                    y=ap_state,
                    mode="lines",
                    name=signals_obj._properties[signals_obj.Columns.AP_STATE],
                )
            )
            self.fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), xaxis_title="Time[s]")

            plot_titles.append("Values for APState and NumValidParkingBoxes:")
            plots.append(self.fig)
            remarks.append("")

            for plot, plot_title, remark in zip(plots, plot_titles, remarks):
                if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                    self.result.details["Plots"].append(
                        f"<h2>{plot_title}</h2>{plot.to_html(full_html=False, include_plotlyjs=False)}<p>{remark}</p>"
                    )
                else:
                    self.result.details["Plots"].append(f"<h2>{plot_title}</h2>{plot}<p>{remark}</p>")
        except Exception as err:
            print(str(err))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")


@verifies("ReqId_1405820")
@testcase_definition(
    name="SI ParkingBoxVisibleParkIn",
    description="Checks if in Maneuvering Mode, the SceneInterpretation provides only the parking box which was selected by the driver for park in maneuver.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_PbVFkMG3Ee6dXtpGPW5AvA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
@register_inputs("/Playground_2/TSF-Debug")
class SI_ParkingBoxVisibleParkInTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_ParkingBoxVisibleParkIn,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\erg_dana_new_23_09\PFS_FusionAndTracking_pm-ps.erg"

    debug(
        SI_ParkingBoxVisibleParkInTC,
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
