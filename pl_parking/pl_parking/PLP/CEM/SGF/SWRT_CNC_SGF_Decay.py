"""SGF Output Decay TestCase."""

import logging

from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
import os
import sys

import pandas as pd
from tsf.core.results import DATA_NOK

TRC_ROOT = os.path.abspath(os.path.join(__file__, "", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
TSF_BASE = os.path.abspath(os.path.join(__file__, "", "..", "..", "..", "..", ".."))
if TSF_BASE not in sys.path:
    sys.path.append(TSF_BASE)


import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals

SIGNAL_DATA = "SGF_Output_Decay"

example_obj = SGFSignals()


@teststep_definition(
    step_number=1,
    name="CEM-SGF Decay",
    description="This test case checks if in case new sensor measurements contradict to the previous measurements, SGF decays Static Objects, which were detected in earlier SGF executions.",
    doors_url="",
    expected_result=BooleanResult(TRUE),
)
@register_signals(SIGNAL_DATA, SGFSignals)
class TestStepFtSGFDecay(TestStep):
    """TestStep for SGF Decaying, utilizing a custom report."""

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize object attributes."""
        super().__init__()

    @staticmethod
    def find_object_index(string, separator):
        """The function extracts the index from and indexed column name."""
        index = ""
        # Find the position of the character
        pos = string.find(separator)
        # Get the substring after the character
        if pos != -1:
            substring = string[pos + 1 :]
            index = substring.strip()
        return index

    def process(self, **kwargs):
        """The function processes signals data to evaluate certain conditions and generate plots and remarks based on
        the evaluation results.
        """
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        plot_titles, plots, remarks = rep([], 3)
        signal_summary = {}
        # Initializing the result with data nok
        self.result.measured_result = DATA_NOK

        reader = self.readers[SIGNAL_DATA]
        data_df = reader.as_plain_df
        data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in data_df.columns]
        # filter only valid outputs
        data_df = data_df[data_df["SGF_sig_status"] == 1]
        number_of_objects = data_df["numPolygons"]
        max_num_of_objects = number_of_objects.max()

        if max_num_of_objects >= 1:
            # if False:    # dummy data for testing without proper recording
            evaluation = " Measurement has more than one static object."
            signal_summary["SGF_Decay"] = evaluation
            test_result = fc.NOT_ASSESSED
        elif max_num_of_objects == 0:
            evaluation = " Measurement has no static object."
            signal_summary["SGF_Decay"] = evaluation
            test_result = fc.NOT_ASSESSED
        elif max_num_of_objects == 1:
            # elif True:    # dummy data for testing without proper recording
            obj_id_col = [col for col in data_df.columns if "polygonId" in col and data_df[col].any()]
            if len(obj_id_col) > 1:
                # if False:    # dummy data for testing without proper recording
                # evaluation = f" Measurement has more than one static object in the timestamp {row["SGF_timestamp"]}."
                evaluation = " Measurement has more than one static object."
                signal_summary["SGF_Decay"] = evaluation
                test_result = fc.NOT_ASSESSED
            else:
                col_name = (
                    "polygonId_0"  # dummy data for testing (this should be the real column name in the real data also)
                )
                obj_index = self.find_object_index(col_name, "_")
                # Check if the object is there in the last row
                if data_df[col_name].iloc[-1] == 0:
                    # if False:    dummy data for testing without proper recording
                    # the object disapeared, the test PASSES
                    evaluation = " SGF decays Static Objects, which were detected in earlier SGF executions.."
                    signal_summary["SGF_Decay"] = evaluation
                    test_result = fc.PASS
                else:
                    # Select the maximum of all further ecistence probabilty values from this columns
                    max_existence_prob = data_df["existenceProbability_" + obj_index].max()
                    # Select the last existence probability
                    last_existence_prob = data_df["existenceProbability_" + obj_index].iloc[-1]
                    # If the max is greater or equal than the last one, the test FAILS, else it PASSES
                    if last_existence_prob < max_existence_prob:
                        evaluation = " SGF decays Static Objects, which were detected in earlier SGF executions."
                        signal_summary["SGF_Decay"] = evaluation
                        test_result = fc.PASS
                    else:
                        evaluation = (
                            " SGF does not decays Static Objects, which were detected in earlier SGF executions."
                        )
                        signal_summary["SGF_Decay"] = evaluation
                        test_result = fc.FAIL

        # Set table dataframe
        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": "Check if in case new sensor measurements contradict to the previous measurements, SGF decays Static Objects, which were detected in earlier SGF executions."
                },
                "Result": {"1": evaluation},
                "Verdict": {"1": test_result},
            }
        )

        sig_sum = fh.build_html_table(signal_summary, table_title="SGF Decay")
        self.result.details["Plots"].append(sig_sum)

        result_df = {
            "Verdict": {"value": test_result.title(), "color": fh.get_color(test_result)},
            fc.REQ_ID: ["1995556"],
            fc.TESTCASE_ID: ["91193"],
            fc.TEST_SAFETY_RELEVANT: [fc.NOT_AVAILABLE],
            fc.TEST_DESCRIPTION: [
                "Verify if an Init request is received, SGF shall reset its internal state and determine its output based on sensor information received only after the Init request."
            ],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        elif test_result == fc.NOT_ASSESSED:
            self.result.measured_result = DATA_NOK
        else:
            self.result.measured_result = FALSE

        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df


@verifies("1995556")
@testcase_definition(
    name="SWRT_CNC_SGF_Decay",
    description="This test case checks if in case new sensor measurements contradict to the previous measurements, SGF decays Static Objects, which were detected in earlier SGF executions.",
    doors_url="https://jazz.conti.de/rm4/web#action=com.ibm.rdm.web.pages.showArtifactPage&artifactURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Fresources%2FBI_8X2hcN-uEe62R7UY0u3jZg&componentURI=https%3A%2F%2Fjazz.conti.de%2Frm4%2Frm-projects%2F_D9K28PvtEeqIqKySVwTVNQ%2Fcomponents%2F_tpTA4CuJEe6mrdm2_agUYg&oslc.configuration=https%3A%2F%2Fjazz.conti.de%2Fgc%2Fconfiguration%2F36325",
)
class FtSGFDecay(TestCase):
    """CEM-SGF Decay Test Case"""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Define the test steps."""
        return [TestStepFtSGFDecay]
