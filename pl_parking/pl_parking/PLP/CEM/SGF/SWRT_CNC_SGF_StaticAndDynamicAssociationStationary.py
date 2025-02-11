"""Example functional test"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..", ".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition,
)

"""imports from current repo"""
import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import (
    MfCustomTestcaseReport,
    MfCustomTeststepReport,
)
from pl_parking.PLP.CEM.SGF.ft_helper import SGFSignals
from pl_parking.PLP.CEM.TPF.ft_helper import TPFSignals

###----------------

###----------------

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "STATIC_AND_DYNAMIC_ASSOCIATION_STATIONARY"
TPF_ALIAS = "TPF_STATIC_AND_DYNAMIC_ASSOCIATION_STATIONARY"

sgf_obj = SGFSignals()
tpf_obj = TPFSignals()

"""Each test step should have a test step definition.
This will include step_ number, name, a short description and the type of expected result."""


@teststep_definition(
    step_number=1,
    name="Static and dynamic association stationary",  # this would be shown as a test step name in html report
    description=(
        "This test case checks if a Traffic Participant is detected by SGF as a Static Object AND \
        TPF provides it as a Fused Traffic Participant too AND the FTP’s moving_flag=STATIONARY, \
        SGF shall provide the corresponding Static Object, \
        and set the Static Objects's associatedDynamicObjectId to the corresponding FTP ID."
    ),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, SGFSignals)
@register_signals(TPF_ALIAS, TPFSignals)
class TestStepFtStaticAndDynamicAssociationStationary(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    Check requirement 1522145: If a Traffic Participant is detected by SGF as a Static Object \
        AND TPF provides it as a Fused Traffic Participant too AND the FTP’s moving_flag=STATIONARY, \
        SGF shall provide the corresponding Static Object, and set the Static Objects's associatedDynamicObjectId \
        to the corresponding FTP ID.

    Detail
    ------

        "This test case checks if a Traffic Participant is detected by SGF as a Static Object AND \
        TPF provides it as a Fused Traffic Participant too AND the FTP’s moving_flag=STATIONARY, \
        SGF shall provide the corresponding Static Object, \
        and set the Static Objects's associatedDynamicObjectId to the corresponding FTP ID."
    """

    custom_report = MfCustomTeststepReport  # Specific overview

    def __init__(self):
        """Initialize the teststep."""
        super().__init__()

    #
    def process(self, **kwargs):
        """
        The function processes signals data to evaluate certain conditions and generate plots and remarks based on the
        evaluation results.
        """  # required docstring
        _log.debug("Starting processing...")
        # Update the details from the results page with the needed information
        # All the information from self.result.details is transferred to report maker(MfCustomTeststepReport in our case)
        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )
        #  time_threshold = None
        # signal_name = signals_obj._properties
        # Make a constant with the reader for signals:
        self.test_result = fc.INPUT_MISSING  # Result
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        signal_summary = {}  # Initializing the dictionary with data for final evaluation table
        positive_associations = []
        not_associated = []

        # Load signals
        sgfReader = self.readers[ALIAS]
        sgf_data_df = sgfReader.as_plain_df
        sgf_data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in sgf_data_df.columns]

        # filter only valid outputs
        sgf_data_df = sgf_data_df[sgf_data_df["SGF_sig_status"] == 1]
        sgf_data_df = sgf_data_df[sgf_data_df["numPolygons"] > 0]

        tpfReader = self.readers[TPF_ALIAS]
        tpf_data_df = tpfReader.as_plain_df
        tpf_data_df.columns = [f"{col[0]}_{col[1]}" if type(col) is tuple else col for col in tpf_data_df.columns]

        sgfObjectIds = sgf_data_df.loc[
            :, sgf_data_df.columns.str.contains("polygonId")
        ]  # a Traffic Participant is detected by SGF as a Static Object
        sgfIs_Associated = sgf_data_df.loc[:, sgf_data_df.columns.str.contains("isAssociated")]
        sgfAssociatedDynamicObjectId = sgf_data_df.loc[:, sgf_data_df.columns.str.contains("associatedDynamicObjectId")]
        tpfObjectIds = tpf_data_df.loc[:, tpf_data_df.columns.str.contains(".id")]
        tpfDynamicProperties = tpf_data_df.loc[:, tpf_data_df.columns.str.contains(".dynamicProperty")]
        tpfDynamicProperties[(tpfDynamicProperties == 2).any(axis="columns")]

        for i, columnName in enumerate(sgfObjectIds):
            for sgfAssociatiedTuple in enumerate(sgfIs_Associated.values[i]):
                if (
                    sgfObjectIds[columnName].values[i] != 0 and sgfIs_Associated.values[sgfAssociatiedTuple] == 1
                ):  # a Traffic Participant is detected by SGF as a Static Object
                    for j, tpfObjId in enumerate(tpfObjectIds):  # TPF provides it as a Fused Traffic Participant
                        if tpfDynamicProperties.values[j] == 2:  # FTP’s moving_flag=STATIONARY
                            if (
                                sgfAssociatedDynamicObjectId.values[i] == tpfObjId
                            ):  # set the Static Objects's associatedDynamicObjectId to the corresponding FTP ID.
                                positive_associations.append(sgfObjectIds["columnName"])
                            else:
                                if sgfObjectIds[columnName].values[i] not in not_associated:
                                    not_associated.append(sgfObjectIds[columnName].values[i])
                        else:
                            if sgfObjectIds[columnName].values[i] not in not_associated:
                                not_associated.append(sgfObjectIds[columnName].values[i])
                else:
                    if sgfObjectIds[columnName].values[i] not in not_associated:
                        not_associated.append(sgfObjectIds[columnName].values[i])

        if (len(positive_associations) > 0) and (len(positive_associations) == len(tpfDynamicProperties)):
            evaluation = "The evaluation <b>PASSED</b> because all Traffic Participant detected by SGF as a Static Object, \
                having a moving state = STATIONARY is provided as a Static Object and has set the Static Objects's associatedDynamicObjectId \
                the corresponding FTP ID."
            self.result.measured_result = TRUE
        else:
            evaluation = "The evaluation <b>FAILED</b> ."
            self.result.measured_result = FALSE

        signal_summary[0] = evaluation
        remark = " ".join(
            f"Check that after .planningCtrlPort.apStates == {constants.GeneralConstants.AP_AVG_ACTIVE_IN}, the \
            speed does not exceed the accepted value.".split()
        )
        # The signal summary and observations will be converted to pandas and finally the html table will be created with them
        self.sig_sum = fh.convert_dict_to_pandas(signal_summary, remark)
        plots.append(self.sig_sum)

        # Add the plots in html page
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)


# Define the test case definition. This will include the name of the test case and a description of the test.
@testcase_definition(
    name="Static and dynamic association stationary",
    description=(
        "This test case checks if a Traffic Participant is detected by SGF as a Static Object AND \
        TPF provides it as a Fused Traffic Participant too AND the FTP’s moving_flag=STATIONARY, \
        SGF shall provide the corresponding Static Object, \
        and set the Static Objects's associatedDynamicObjectId to the corresponding FTP ID."
    ),
    doors_url="https://jazz.conti.de/qm4/web/console/LIB_L3_SW_TM/_or7dMJpREe6OHr4fEH59Xg#action=com.ibm.rqm.planning.home.actionDispatcher&subAction=viewTestCase&id=39241",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestStaticAndDynamicAssociationStationaryFT(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [TestStepFtStaticAndDynamicAssociationStationary]  # in this list all the needed test steps are included
