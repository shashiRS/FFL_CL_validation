#!/usr/bin/env python3
"""This is the test case to get calculate ConfusionMatrixWithFrontCameraBlockage"""

"""import libraries"""
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
from tsf.core.results import FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
    verifies,
)
from tsf.io.signals import SignalDefinition

"""imports from current repo"""
from tsf.core.utilities import debug

import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport, rep

__author__ = "uif65342"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

"""any test must have a specific and UNIQUE alias as it will contain a data frame
with all the signals for a test script"""
READER_NAME = "ConfusionMatrixWithFrontCameraBlockageReader"


class Signals(SignalDefinition):
    """Signal definition."""

    """in this class you can define the signals which you will need for test
       and which would be extracted from measurement"""

    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TimeStamp = "TimeStamp"
        FC_detectionStatus = "FC_detectionStatus"
        LSC_detectionStatus = "LSC_detectionStatus"
        RC_detectionStatus = "RC_detectionStatus"
        RSC_detectionStatus = "RSC_detectionStatus"

    def get_properties(self):
        """Generate a string of signals to be read."""
        signal_dict = {}
        signal_dict[self.Columns.TimeStamp] = ".Package.TimeStamp"
        signal_dict[self.Columns.FC_detectionStatus] = ".BD_FC.pBlockageOutput.sFullBlockage.detectionStatus"
        signal_dict[self.Columns.LSC_detectionStatus] = ".BD_LSC.pBlockageOutput.sFullBlockage.detectionStatus"
        signal_dict[self.Columns.RC_detectionStatus] = ".BD_RC.pBlockageOutput.sFullBlockage.detectionStatus"
        signal_dict[self.Columns.RSC_detectionStatus] = ".BD_RSC.pBlockageOutput.sFullBlockage.detectionStatus"
        # signal_dict[self.Columns.SIGTIMESTAMP] = ".CB_FC.CbObject.sSigHeader.uiTimeStamp"
        return signal_dict

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = [
            "AP",
            "ADC5xx_Device",
            "M7board.EM_Thread",
            "CarPC.EM_Thread",
            "MTS",
            "SIM VFB",
        ]

        self._properties = self.get_properties()


signals_obj = Signals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Test step to calculate ConfusionMatrix With FrontCamera Blockage",  # this would be shown as a test step name in html report
    description=(
        "Test step to calculate ConfusionMatrix With FrontCamera Blockage"
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(READER_NAME, Signals)
class ConfusionMatrixWithFrontCameraBlockage(TestStep):
    """Test step to calculate ConfusionMatrix With FrontCamera Blockage

    Objective
    ---------
    Test step to calculate ConfusionMatrix With FrontCamera Blockage


    Detail
    ------
    Test step to calculate ConfusionMatrix With FrontCamera Blockage

    """

    custom_report = MfCustomTeststepReport

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    def process(self, **kwargs):
        """Process the test result."""
        _log.debug("Starting processing...")

        """
        Method calculate_crosstab_RC_LSC_RSC to calculate True Positive here for cameras RC, LSC, RSC
        """

        def calculate_crosstab_RC_LSC_RSC(self, reader_DF, signalName_to_process):
            """Create runtime temp csv"""
            your_file_name_RC_LSC_RSC = f"your_file_{signalName_to_process}.csv"
            reader_DF.to_csv(your_file_name_RC_LSC_RSC, index=False)
            reader_DF = pd.read_csv(your_file_name_RC_LSC_RSC)

            y_true = reader_DF["GT_RC_LSC_RSC"]
            y_pred = reader_DF[signalName_to_process]

            if os.path.exists(your_file_name_RC_LSC_RSC):
                os.remove(your_file_name_RC_LSC_RSC)
            else:
                print(f"The file {your_file_name_RC_LSC_RSC} does not exist")

            """
            crosstab to calculate confusion matrix , Here getting TP only (as all matching GT and predicted values) ,
            converting to list and returning it.
            """

            crosstab_val = pd.crosstab(y_true, y_pred)
            crosstab_val = crosstab_val.values[0].tolist()
            return crosstab_val

        """Reading all signals from readers """
        reader_DF = self.readers[READER_NAME].signals

        """ adding column with Front camera  GT values as 1 """
        reader_DF["GT_FC"] = reader_DF.apply(lambda GT_FC: 1, axis=1)

        """ adding column with Rear camera , Left side Camera,
        Right Side camera, Rear camera GT values as 0 """

        reader_DF["GT_RC_LSC_RSC"] = reader_DF.apply(lambda GT_RC_LSC_RSC: 0, axis=1)
        self.result.details.update(
            {
                "Plots": [],
                "Plot_titles": [],
                "Remarks": [],
                "file_name": os.path.basename(self.artifacts[0].file_path),
            }
        )

        test_result = fc.PASS
        """plots and remarks need to have the same length """
        plot_titles, plots, remarks = rep([], 3)

        """get unique value from column  GroundTruth """
        unique_GroundTruth = reader_DF["GT_FC"].unique()

        """ convert numpy GroundTruth array to list """
        unique_GroundTruth_list = list(unique_GroundTruth)

        try:
            # column_names = reader_DF.columns
            unique_fDetection = reader_DF["FC_detectionStatus"].unique()
            """convert numpy fDetection array to list"""
            unique_fDetection_list = list(unique_fDetection)
        except Exception as e:
            print(f"Exception found as : {e}")

        """ for labels joined and get unique values from lists unique_GroundTruth_list
        and unique_fDetection_list
        """
        labels_list = list(set(unique_GroundTruth_list + unique_fDetection_list))
        """sort labels """
        labels_list.sort()

        reader_DF.to_csv("your_file_name.csv", index=False)
        reader_DF = pd.read_csv("your_file_name.csv")

        y_true = reader_DF["GT_FC"]
        y_pred = reader_DF["FC_detectionStatus"]

        """ remove temp file """
        if os.path.exists("your_file_name.csv"):
            os.remove("your_file_name.csv")
        else:
            print("The file 'your_file_name.csv' does not exist")

        labels = labels_list

        """ confusion_matrix calculation"""
        cross_tab = pd.crosstab(y_true, y_pred)
        """ convert to data frame """
        cm_df = pd.DataFrame(cross_tab, index=labels, columns=labels)
        """ convert value NA to 0 in dataframe """
        cm_df = cm_df.fillna(0)
        """ convert value float to INT in dataframe """
        cm_df = cm_df.astype(int)

        TN = cm_df.iloc[0].tolist()[0]
        FP = cm_df.iloc[0].tolist()[1]
        FN = cm_df.iloc[1].tolist()[0]
        TP = cm_df.iloc[1].tolist()[1]

        N = FP + TN
        P = TP + FN
        if P:
            TPR = TP / P
            FPR = FP / P

        if N:
            TNR = TN / N
            FNR = FN / N

        """ Confusion Matrix Bar Chart """
        Matrix_name = ["TN", "FP", "FN", "TP"]

        Matrix_values = [TN, FP, FN, TP]

        fig1 = go.Figure(
            data=[
                go.Bar(
                    x=Matrix_name,
                    y=Matrix_values,
                    hovertext=["Matrix_name", "Matrix_values"],
                    text=Matrix_values,
                    textposition="auto",
                )
            ]
        )

        fig1.update_traces(
            marker_color="rgb(158,202,225)",
            marker_line_color="rgb(8,48,107)",
            marker_line_width=1.5,
            opacity=0.6,
        )
        fig1.update_layout(title_text="Bar chart for FC_detectionStatus")

        if N and P:
            """Confusion Matrix Bar Chart"""
            Matrix_Name_Rate = ["TPR", "FPR", "TNR", "FNR"]
            Matrix_Name_Values = [TPR, FPR, TNR, FNR]

            fig2 = go.Figure(
                data=[
                    go.Bar(
                        x=Matrix_Name_Rate,
                        y=Matrix_Name_Values,
                        hovertext=["Matrix_Name_Rate", "Matrix_Name_Values"],
                        text=Matrix_Name_Values,
                        textposition="auto",
                    )
                ]
            )

            fig2.update_traces(
                marker_color="rgb(158,202,225)",
                marker_line_color="rgb(8,48,107)",
                marker_line_width=1.5,
                opacity=0.6,
            )
            fig2.update_layout(title_text="Bar chart for FC_detectionStatus Rate")

        elif P:
            """Confusion Matrix Bar Chart"""
            Matrix_Name_Rate = ["TPR", "FPR"]
            Matrix_Name_Values = [TPR, FPR]

            fig2 = go.Figure(
                data=[
                    go.Bar(
                        x=Matrix_Name_Rate,
                        y=Matrix_Name_Values,
                        hovertext=["Matrix_Name_Rate", "Matrix_Name_Values"],
                        text=Matrix_Name_Values,
                        textposition="auto",
                    )
                ]
            )

            fig2.update_traces(
                marker_color="rgb(158,202,225)",
                marker_line_color="rgb(8,48,107)",
                marker_line_width=1.5,
                opacity=0.6,
            )
            fig2.update_layout(title_text="Bar chart for FC_detectionStatus Rate")

        elif N:
            """Confusion Matrix Bar Chart"""
            Matrix_Name_Rate = ["TNR", "FNR"]
            Matrix_Name_Values = [TNR, FNR]

            fig2 = go.Figure(
                data=[
                    go.Bar(
                        x=Matrix_Name_Rate,
                        y=Matrix_Name_Values,
                        hovertext=["Matrix_Name_Rate", "Matrix_Name_Values"],
                        text=Matrix_Name_Values,
                        textposition="auto",
                    )
                ]
            )

            fig2.update_traces(
                marker_color="rgb(158,202,225)",
                marker_line_color="rgb(8,48,107)",
                marker_line_width=1.5,
                opacity=0.6,
            )
            fig2.update_layout(title_text="Bar chart for FC_detectionStatus Rate")

        """
        Accuracy is used to measure the performance of the model. It is the ratio of Total correct instances to the total instances.
        Accuracy=(TP+TN)/(TP+TN+FP+FN)
        print(f"Accuracy is : {Accuracy}")

        """
        Accuracy = (TP + TN) / (TP + TN + FP + FN)

        """
        Precision is a measure of how accurate a model’s positive predictions are. It is defined as the ratio
        of true positive predictions to the total number of positive predictions made by the model.
        Precision=TP/(TP+FP)

        """
        Precision = TP / (TP + FP)

        """
        Recall measures the effectiveness of a classification model in identifying all relevant instances from a dataset.
        It is the ratio of the number of true positive (TP) instances to the sum of true positive and false negative (FN) instances.
        Recall=TP/(TP+FN)
        """
        Recall = TP / (TP + FN)

        """
        F1-score is used to evaluate the overall performance of a classification model. It is the harmonic mean of precision and recall,
        F1-Score=(2*Precision*Recall)/(Precision+Recall)
        """
        F1_Score = (2 * Precision * Recall) / (Precision + Recall)

        """
        Specificity is another important metric in the evaluation of classification models, particularly in binary classification.
        It measures the ability of a model to correctly identify negative instances. Specificity is also known as the True Negative Rate.
        Formula is given by:
        Specificity=TN/(TN+FP)

        """
        """  Matrix for Accuracy, Precision, Recall, F1_Score """
        Matrix_Name_A_P_R_F1 = ["Accuracy", "Precision", "Recall", "F1_Score"]
        Matrix_Name_A_P_R_F1_Values = [Accuracy, Precision, Recall, F1_Score]

        fig3 = go.Figure(
            data=[
                go.Bar(
                    x=Matrix_Name_A_P_R_F1,
                    y=Matrix_Name_A_P_R_F1_Values,
                    hovertext=["Matrix_Name_A_P_R_F1", "Matrix_Name_A_P_R_F1_Values"],
                    text=Matrix_Name_A_P_R_F1_Values,
                    textposition="auto",
                )
            ]
        )

        fig3.update_traces(
            marker_color="rgb(158,202,225)",
            marker_line_color="rgb(8,48,107)",
            marker_line_width=1.5,
            opacity=0.6,
        )
        fig3.update_layout(title_text="FC_detectionStatus Matrix for  Accuracy, Precision, Recall, F1_Score")

        """ called method calculate_crosstab_RC_LSC_RSC
        to calculate confusion matrix for camera RC, LSC, RSC
        """
        detectionNameList = [
            "LSC_detectionStatus",
            "RC_detectionStatus",
            "RSC_detectionStatus",
        ]
        detectionNameListValue = []
        for each_detectionNameList in detectionNameList:
            signalName_to_process = each_detectionNameList
            retuen_val = calculate_crosstab_RC_LSC_RSC(self, reader_DF, signalName_to_process)
            detectionNameListValue.append(retuen_val)

        flat_list = []
        for sublist in detectionNameListValue:
            for element in sublist:
                flat_list.append(element)

        """ Confusion Matrix Bar Chart """
        fig4 = go.Figure(
            data=[
                go.Bar(
                    x=detectionNameList,
                    y=flat_list,
                    hovertext=["detectionNameList", "flat_list"],
                    text=flat_list,
                    textposition="auto",
                )
            ]
        )

        fig4.update_traces(
            marker_color="rgb(158,202,225)",
            marker_line_color="rgb(8,48,107)",
            marker_line_width=1.5,
            opacity=0.6,
        )
        fig4.update_layout(title_text="for camera LSC_RC_RSC Confusion Matrix True Positive Bar Chart")

        plot_titles.append("Test Confusion Matrix report")
        plots.append(fig1)
        plots.append(fig2)
        plots.append(fig3)
        plots.append(fig4)
        remarks.append("No matching output was found")

        result_df = {
            "Verdict": {
                "value": test_result.title(),
                "color": fh.get_color(test_result),
            },
            fc.REQ_ID: ["TODO"],
            fc.TESTCASE_ID: ["L3_TPP_41582"],
            fc.TEST_SAFETY_RELEVANT: ["TODO"],
            fc.TEST_DESCRIPTION: ["TODO"],
            fc.TEST_RESULT: [test_result],
        }

        if test_result == fc.PASS:
            self.result.measured_result = TRUE
        else:
            self.result.measured_result = FALSE
        for plot in plots:
            self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)

        self.result.details["Additional_results"] = result_df

        """Add the data in the table from Functional Test Filter Results"""
        additional_results_dict = {
            "Verdict": {
                "value": test_result.title(),
                "color": fh.get_color(test_result),
            },
        }
        self.result.details["Additional_results"] = additional_results_dict


@verifies("ReqId_2401347")
@testcase_definition(
    name="Test case for confusion_matrix for FC_Blockage",
    description=("This an example of test case of confusion_matrix for FC_Blockage"),
)
@register_inputs("/parking")
class ConfusionMatrixWithFrontCameraBlockageTestCase(TestCase):
    """Example test case."""

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""
        return [ConfusionMatrixWithFrontCameraBlockage]


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Call to debug to set up debugging in the simplest possible way.

    When calling the test case you need to provide a valid input to

    execute the test (e.g. a BSIG file) and report the result.

    This is only meant to jump start testcase debugging.

    """
    debug(
        ConfusionMatrixWithFrontCameraBlockageTestCase,
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
