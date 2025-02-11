"""
This module defines a test case and test step for verifying the persistence of a parking box.
Classes:
    SI_ParkInPersistence: A test step that checks if a parking box remains persistent during the parking process.
    SI_ParkInPersistenceTC: A test case that includes the SI_ParkInPersistence test step.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

# import seaborn as sns
import pandas as pd
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
    name="Check for SI_ParkInPersistence",
    description="Checks if a valid parking box in consistently offered during the parking process.",
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, SISignals)
class SI_ParkInPersistence(TestStep):
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
            # Get the read data frame
            test_result = fc.FAIL
            read_data = self.readers[READER_NAME]
            non_persistent_timestamps = []
            park_in_persistent = False

            df = read_data.as_plain_df
            df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in df.columns]

            ap_state = df[SISignals.Columns.AP_STATE]
            ap_time = df[SISignals.Columns.TIME].values.tolist()
            ap_time = [round(i, 3) for i in ap_time]

            num_valid_pb = df[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU]
            ap_state = ap_state.values.tolist()

            cond_1 = f"ApState should indicate AP_AVG_ACTIVE_IN({AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN}) during the parking process."
            cond_2 = f"ApState should transition to AP_AVG_FINISHED({AUPConstants.AP_STATES.AP_AVG_FINISHED}) once the maneuver is complete."
            cond_3 = (
                f"ApParkingBox must remain non-zero while ApState is AP_AVG_ACTIVE_IN({AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN}) "
                f"and until it transitions to AP_AVG_FINISHED({AUPConstants.AP_STATES.AP_AVG_FINISHED})."
            )

            conditions_table = pd.DataFrame(
                {
                    "Conditions": {
                        "1": cond_1,
                        "2": cond_2,
                        "3": cond_3,
                    },
                },
            )
            cond_table = go.Figure(
                data=[
                    go.Table(
                        header=dict(
                            values=list(conditions_table.columns),
                            fill_color="rgb(255,165,0)",
                            font=dict(size=12, family="Arial", color="rgb(0,0,0)"),
                        ),
                        cells=dict(
                            height=50,
                            values=[conditions_table[col] for col in conditions_table.columns],
                            align="center",
                            font=dict(size=12),
                        ),
                    )
                ]
            )
            plot_titles.append("")
            plots.append(cond_table)
            remarks.append("")

            start_idx_list = df.index[
                df[SISignals.Columns.AP_STATE] == AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN
            ].tolist()
            start_idx = start_idx_list[0] if start_idx_list else None

            end_idx_list = df.index[
                (df.index > start_idx) & (df[SISignals.Columns.AP_STATE] == AUPConstants.AP_STATES.AP_AVG_FINISHED)
            ].tolist()
            end_idx = end_idx_list[0] if end_idx_list else None

            if start_idx is not None and end_idx is not None:
                park_in_persistent = df.loc[start_idx:end_idx, SISignals.Columns.NUMVALIDPARKINGBOXES_NU].eq(1).all()

                if not park_in_persistent:
                    _log.debug("Parking box is not park-in-persistent.")
                    non_persistent_timestamps = df.loc[start_idx:end_idx][
                        df.loc[start_idx:end_idx, signals_obj.Columns.NUMVALIDPARKINGBOXES_NU] == 0
                    ].index.tolist()

            evaluation1 = " ".join(
                f"The evaluation of {signals_obj._properties[SISignals.Columns.AP_STATE]} is FAILED, \
                    the value <b>AP_AVG_ACTIVE_IN({AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN})</b> was never found.".split()
            )
            evaluation2 = " ".join(
                f"The evaluation of {signals_obj._properties[SISignals.Columns.AP_STATE]} is FAILED, \
                    the value <b>AP_AVG_FINISHED({AUPConstants.AP_STATES.AP_AVG_FINISHED})</b> was never found.".split()
            )
            evaluation3 = " ".join(
                f"The evaluation of {signals_obj._properties[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU][0]} could not \
                    be evaluated due to the absence of values \
                        <b>AP_AVG_ACTIVE_IN({AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN})</b> or \
                            <b>AP_AVG_FINISHED({AUPConstants.AP_STATES.AP_AVG_FINISHED})</b> in \
                                {signals_obj._properties[SISignals.Columns.AP_STATE]}.".split()
            )

            if start_idx is not None:
                if end_idx is not None:
                    for timestamp_val in df.index:
                        if timestamp_val not in non_persistent_timestamps:
                            test_result = fc.PASS
                            evaluation3 = " ".join(
                                f"The evaluation of {signals_obj._properties[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU][0]} is PASSED, \
                                    the value <b>0 was not found</b> in the range \
                                        of {round(df[SISignals.Columns.TIME][start_idx], 2)}s - {round(df[SISignals.Columns.TIME][end_idx], 2)} s\
                                            ({start_idx} to {end_idx}.".split()
                            )
                        else:
                            test_result = fc.FAIL
                            evaluation3 = " ".join(
                                f"The evaluation of {signals_obj._properties[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU][0]} is FAILED, \
                                    the value <b>0 was found</b> at timestamp \
                                        {round(df[SISignals.Columns.TIME][timestamp_val], 2)}s ({timestamp_val}).".split()
                            )
                            break
                    evaluation2 = " ".join(
                        f"The evaluation of {signals_obj._properties[SISignals.Columns.AP_STATE]} is PASSED, \
                            the value of <b>AP_AVG_FINISHED({AUPConstants.AP_STATES.AP_AVG_FINISHED})</b> was found at \
                                timestamp {round(df[SISignals.Columns.TIME][end_idx], 2)}s ({end_idx}).".split()
                    )
                evaluation1 = " ".join(
                    f"The evaluation of {signals_obj._properties[SISignals.Columns.AP_STATE]} is PASSED, \
                        the value of <b>AP_AVG_ACTIVE_IN({AUPConstants.AP_STATES.AP_AVG_ACTIVE_IN})</b> was found at \
                            timestamp {round(df[SISignals.Columns.TIME][start_idx], 2)}s ({start_idx}).".split()
                )

            signal_summary[f"{signals_obj._properties[SISignals.Columns.AP_STATE]} - AP_AVG_ACTIVE_IN"] = evaluation1
            signal_summary[f"{signals_obj._properties[SISignals.Columns.AP_STATE]} - AP_AVG_FINISHED"] = evaluation2
            signal_summary[signals_obj._properties[signals_obj.Columns.NUMVALIDPARKINGBOXES_NU][0]] = evaluation3

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


@verifies("ReqId_1863296")
@testcase_definition(
    name="SI Park-In Persistence",
    description="Checks if a valid parking box in consistently offered during the parking process.",
    doors_url=r"https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_PbVFkMG3Ee6dXtpGPW5AvA&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_N-ji4CuIEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
@register_inputs("/Playground_2/TSF-Debug")
class SI_ParkInPersistenceTC(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [
            SI_ParkInPersistence,
        ]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    # test_bsigs = r"D:\reporting-ui\workspace\workspace\pl_parking\recordings\SI_recc\erg_dana_new_23_09\PFS_FusionAndTracking_pm-ps.erg"

    debug(
        SI_ParkInPersistenceTC,
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
