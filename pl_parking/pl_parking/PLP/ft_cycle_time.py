"""Example functional test"""  # this is a required docstring

"""import libraries"""
import logging
import os
import sys

import plotly.graph_objects as go

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
    register_inputs,
    register_signals,
    testcase_definition,
    teststep_definition,
)
from tsf.io.signals import SignalDefinition

"""imports from current repo"""
import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport
from pl_parking.PLP.constants import CycleTimeConstants as CYCLE_TIME_CONSTANTS
from pl_parking.PLP.constants import ThresholdTimeConstants as THRESHOLD_TIME_CONSTANTS

__author__ = "A AM SB PRK IAS LAT1"
__copyright__ = "2020-2012, Continental AG"
__version__ = "0.16.1"
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# any test must have a specific and UNIQUE alias as it will contain a data frame with all the signals for a test script
ALIAS = "CYCLE_TIME"


class Signals(SignalDefinition):
    """Signal definition."""

    class Columns(SignalDefinition.Columns):

        TIME_GRAPPA = "TIME_GRAPPA"
        TIME_ISP = "TIME_ISP"
        TIME_LSCA = "TIME_LSCA"
        TIME_TCE = "TIME_TCE"
        TIME_TRJCTL = "TIME_TRJCTL"
        TIME_TRAJPLA = "TIME_TRAJPLA"
        TIME_OFC = "TIME_OFC"
        TIME_SI = "TIME_SI"
        TIME_SPP = "TIME_SPP"
        TIME_TPP = "TIME_TPP"
        TIME_US = "TIME_US"
        TIME_VEDODO = "TIME_VEDODO"
        TIME_CHIPS_PYRAMID = "TIME_CHIPS_PYRAMID"
        TIME_CHIPS_CYLINDRICAL = "TIME_CHIPS_CYLINDRICAL"
        TIME_OFT = "TIME_OFT"
        TIME_GDR = "TIME_GDR"
        TIME_EMO = "TIME_EMO"
        TIME_PMSD = "TIME_PMSD"
        TIME_CEM_LSM = "TIME_CEM_LSM"
        TIME_PDW = "TIME_PDW"
        TIME_PARKSM_CORE = "TIME_PARKSM_CORE"
        TIME_APPDEMO_PARKSM = "TIME_APPDEMO_PARKSM"
        TIME_MANAGER = "TIME_MANAGER"
        TIME_WHLPROTECTPROC = "TIME_WHLPROTECTPROC"
        TIME_APPDEMO_DRVWARNSM = "TIME_APPDEMO_DRVWARNSM"
        TIME_DRVWARNSM = "TIME_DRVWARNSM"
        TIME_APPDEMO_TONH = "TIME_APPDEMO_TONH"
        TIME_APPDEMO_HMIH = "TIME_APPDEMO_HMIH"
        TIME_SYNC = "TIME_SYNC"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._properties = {
            self.Columns.TIME_VEDODO: [
                "MTA_ADC5.MF_VEDODO_DATA.OdoDebugPort.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_GRAPPA: [
                "MTA_ADC5.GRAPPA_FC_DATA.DetectionResults.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_ISP: [
                "MTA_ADC5.ISP_FC_IMAGE.SensorFcIspImageUV.signalHeader.uiTimeStamp",
            ],
            self.Columns.TIME_LSCA: [
                "MTA_ADC5.MF_LSCA_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_TCE: [
                "MTA_ADC5.MF_TCE_DATA.TceDebugPort.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_TRJCTL: [
                "MTA_ADC5.MF_TRJCTL_DATA.DrivingResistancePort.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_TRAJPLA: [
                "MTA_ADC5.MF_TRJPLA_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_OFC: [
                "MTA_ADC5.OFC_FC_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_SI: [
                "MTA_ADC5.SI_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_SPP: [
                "MTA_ADC5.SPP_FC_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_TPP: [
                "MTA_ADC5.TPP_FC_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_US: [
                "MTA_ADC5.US_PROCESSING_DATA.UsProcessingDataIntegrity.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_CHIPS_PYRAMID: [
                "MTA_ADC5.CHIPS_W_FC_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_CHIPS_CYLINDRICAL: [
                "MTA_ADC5.CHIPS_FC_CYL_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_OFT: [
                "MTA_ADC5.ARTEMIS_DATA.pOftBasicTracksFront.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_GDR: [
                "MTA_ADC5.ARTEMIS_DATA.gdrPointListLeft.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_EMO: [
                "MTA_ADC5.ARTEMIS_DATA.pEmoCalibrationLeft.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_PMSD: [
                "MTA_ADC5.PMSD_FC_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_CEM_LSM: [
                "MTA_ADC5.CEM200_LSMO_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_PDW: [
                "MTA_ADC5.MF_PDWARNPROC_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_PARKSM_CORE: [
                "MTA_ADC5.MF_PARKSM_CORE_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_APPDEMO_PARKSM: [
                "MTA_ADC5.APPDEMO_PARKSM_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_MANAGER: [
                "MTA_ADC5.MF_MANAGER_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_WHLPROTECTPROC: [
                "MTA_ADC5.APPDEMO_DRVWARNSM_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_APPDEMO_DRVWARNSM: [
                "MTA_ADC5.MF_DRVWARNSM_CORE_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_DRVWARNSM: [
                "MTA_ADC5.MF_DRVWARNSM_CORE_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_APPDEMO_TONH: [
                "MTA_ADC5.APPDEMO_TONH_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_APPDEMO_HMIH: [
                "MTA_ADC5.APPDEMO_HMIH_DATA.m_algoCompState.sSigHeader.uiTimeStamp",
            ],
            self.Columns.TIME_SYNC: [
                "MTA_ADC5.ARTEMIS_DATA.syncRef.m_signalHeader.uiTimeStamp",
            ],
        }


signals_obj = Signals()


@teststep_definition(
    step_number=1,
    name="VEDODO timestamp check",  # this would be shown as a test step name in html report
    description=("VEDODO timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepVEDODOTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_VEDODO, CYCLE_TIME_CONSTANTS.VEDODO_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=2,
    name="GRAPPA timestamp check",  # this would be shown as a test step name in html report
    description=("GRAPPA timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepGRAPPATimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_GRAPPA, CYCLE_TIME_CONSTANTS.GRAPPA_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=3,
    name="TCE timestamp check",  # this would be shown as a test step name in html report
    description=("TCE timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepTCETimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_TCE, CYCLE_TIME_CONSTANTS.TCE_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=4,
    name="TRJCTL timestamp check",  # this would be shown as a test step name in html report
    description=("TRJCTL timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepTRJCTLTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_TRJCTL, CYCLE_TIME_CONSTANTS.TRJCTL_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=5,
    name="ISP timestamp check",  # this would be shown as a test step name in html report
    description=("ISP timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepISPTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_ISP, CYCLE_TIME_CONSTANTS.ISP_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=6,
    name="LSCA timestamp check",  # this would be shown as a test step name in html report
    description=("LSCA timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepLSCATimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_LSCA, CYCLE_TIME_CONSTANTS.LSCA_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=7,
    name="OFC timestamp check",  # this would be shown as a test step name in html report
    description=("OFC timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepOFCTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_OFC, CYCLE_TIME_CONSTANTS.OFC_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=8,
    name="SI timestamp check",  # this would be shown as a test step name in html report
    description=("SI timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepSITimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_SI, CYCLE_TIME_CONSTANTS.SI_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=9,
    name="SPP timestamp check",  # this would be shown as a test step name in html report
    description=("SPP timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepSPPTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_SPP, CYCLE_TIME_CONSTANTS.SPP_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=10,
    name="TPP timestamp check",  # this would be shown as a test step name in html report
    description=("TPP timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepTPPTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_TPP, CYCLE_TIME_CONSTANTS.TPP_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=11,
    name="US timestamp check",  # this would be shown as a test step name in html report
    description=("US timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepUSTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_US, CYCLE_TIME_CONSTANTS.US_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=12,
    name="TRAJPLA timestamp check",  # this would be shown as a test step name in html report
    description=("TRAJPLA timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepTRAJPLATimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_TRAJPLA, CYCLE_TIME_CONSTANTS.TRAJPLA_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=13,
    name="SYNC timestamp check",  # this would be shown as a test step name in html report
    description=("SYNC timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepSYNCTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_SYNC, CYCLE_TIME_CONSTANTS.SYNC_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=14,
    name="CHIPS PYRAMID timestamp check",  # this would be shown as a test step name in html report
    description=("CHIPS PYRAMID timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepCHIPSPYRAMIDTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_CHIPS_PYRAMID, CYCLE_TIME_CONSTANTS.CHIPS_PYRAMID_PROCESSING_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=15,
    name="CHIPS CYLINDRICAL timestamp check",  # this would be shown as a test step name in html report
    description=("CHIPS CYLINDRICAL timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepCHIPSCYLINDRICALTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_CHIPS_CYLINDRICAL, CYCLE_TIME_CONSTANTS.CHIPS_CYLINDRICAL_PROCESSING_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=16,
    name="ARTEMIS OFT timestamp check",  # this would be shown as a test step name in html report
    description=("ARTEMIS OFT timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepOFTTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_OFT, CYCLE_TIME_CONSTANTS.OFT_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=17,
    name="ARTEMIS GDR timestamp check",  # this would be shown as a test step name in html report
    description=("ARTEMIS GDR timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepGDRTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_GDR, CYCLE_TIME_CONSTANTS.GDR_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=18,
    name="ARTEMIS EMO timestamp check",  # this would be shown as a test step name in html report
    description=("ARTEMIS EMO timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepEMOTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_EMO, CYCLE_TIME_CONSTANTS.EMO_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=19,
    name="PMSD timestamp check",  # this would be shown as a test step name in html report
    description=("PMSD timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepPMSDTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_PMSD, CYCLE_TIME_CONSTANTS.PMSD_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=20,
    name="CEM_LSM timestamp check",  # this would be shown as a test step name in html report
    description=("CEM_LSM timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepCEM_LSMTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_CEM_LSM, CYCLE_TIME_CONSTANTS.CEM_LSM_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=21,
    name="PDW timestamp check",  # this would be shown as a test step name in html report
    description=("PDW timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepPDWTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_PDW, CYCLE_TIME_CONSTANTS.PDW_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=22,
    name="PARKSM timestamp check",  # this would be shown as a test step name in html report
    description=("PARKSM timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepPARKSMTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_PARKSM_CORE, CYCLE_TIME_CONSTANTS.PARKSM_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=23,
    name="APPDEMO PARKSM timestamp check",  # this would be shown as a test step name in html report
    description=("APPDEMO PARKSM timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepAPPDEMOPARKSMTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_APPDEMO_PARKSM, CYCLE_TIME_CONSTANTS.APPDEMO_PARKSM_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=24,
    name="MF_MANAGER timestamp check",  # this would be shown as a test step name in html report
    description=("MF_MANAGER timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepMF_MANAGERTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_MANAGER, CYCLE_TIME_CONSTANTS.MF_MANAGER_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=25,
    name="WHLPROTECTPROC timestamp check",  # this would be shown as a test step name in html report
    description=("WHLPROTECTPROC timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepWHLPROTECTPROCTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_WHLPROTECTPROC, CYCLE_TIME_CONSTANTS.WHLPROTECTPROC_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=26,
    name="APPDEMO_DRVWARNSM timestamp check",  # this would be shown as a test step name in html report
    description=("APPDEMO_DRVWARNSM timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepAPPDEMO_DRVWARNSMTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_APPDEMO_DRVWARNSM, CYCLE_TIME_CONSTANTS.WHLPROTECTPROC_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=27,
    name="DRVWARNSM timestamp check",  # this would be shown as a test step name in html report
    description=("DRVWARNSM timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepDRVWARNSMTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_DRVWARNSM, CYCLE_TIME_CONSTANTS.MF_DRVWAENSM_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=28,
    name="APPDEMO_TONH timestamp check",  # this would be shown as a test step name in html report
    description=("APPDEMO_TONH timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepAPPDEMO_TONHTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_APPDEMO_TONH, CYCLE_TIME_CONSTANTS.APPDEMO_TONH_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@teststep_definition(
    step_number=29,
    name="APPDEMO_HMIH timestamp check",  # this would be shown as a test step name in html report
    description=("APPDEMO_HMIH timestamp check."),  # this would be shown as a test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class TestStepAPPDEMO_HMIHTimeCheck(TestStep):
    """testcase that can be tested by a simple pass/fail test.
    This is a required docstring in which you can add more details about what you verify in test step

    Objective
    ---------

    ...

    Detail
    ------

    ...
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

        self.result.details.update(
            {"Plots": [], "Plot_titles": [], "Remarks": [], "file_name": os.path.basename(self.artifacts[0].file_path)}
        )

        # Create empty lists for titles, plots and remarks,if they are needed, plots and remarks need to have the same length
        plot_titles, plots, remarks = fh.rep([], 3)

        self.result.measured_result = DATA_NOK  # Initializing the result with data nok
        df = self.readers[ALIAS]

        self.sig_sum, self.test_result, self.result.measured_result, self.fig, self.fig2 = evaluate_cycle_time(
            df, Signals.Columns.TIME_APPDEMO_HMIH, CYCLE_TIME_CONSTANTS.APPDEMO_HMIH_CYCLE_TIME_MS
        )

        plot_titles.append("")
        plots.append(self.sig_sum)
        remarks.append("")

        if self.fig or self.fig2:
            plot_titles.append("")
            plots.append(self.fig)
            plots.append(self.fig2)
            remarks.append("")
        for plot in plots:
            if "plotly.graph_objs._figure.Figure" in str(type(plot)):
                self.result.details["Plots"].append(plot.to_html(full_html=False, include_plotlyjs=False))
            else:
                self.result.details["Plots"].append(plot)
        for plot_title in plot_titles:
            self.result.details["Plot_titles"].append(plot_title)
        for remark in remarks:
            self.result.details["Remarks"].append(remark)


@register_inputs("/parking")
@testcase_definition(
    name="Cycle time",
    description="This test case verifies the cycle time between timestamps.",
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class TestCycleTime(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [
            TestStepVEDODOTimeCheck,
            TestStepGRAPPATimeCheck,
            TestStepTCETimeCheck,
            TestStepTRJCTLTimeCheck,
            TestStepISPTimeCheck,
            TestStepLSCATimeCheck,
            TestStepOFCTimeCheck,
            TestStepSITimeCheck,
            TestStepSPPTimeCheck,
            TestStepTPPTimeCheck,
            TestStepUSTimeCheck,
            TestStepTRAJPLATimeCheck,
            TestStepSYNCTimeCheck,
            TestStepCHIPSPYRAMIDTimeCheck,
            TestStepCHIPSCYLINDRICALTimeCheck,
            TestStepOFTTimeCheck,
            TestStepGDRTimeCheck,
            TestStepEMOTimeCheck,
            TestStepPMSDTimeCheck,
            TestStepCEM_LSMTimeCheck,
            TestStepPDWTimeCheck,
            TestStepPARKSMTimeCheck,
            TestStepAPPDEMOPARKSMTimeCheck,
            TestStepMF_MANAGERTimeCheck,
            TestStepWHLPROTECTPROCTimeCheck,
            TestStepAPPDEMO_DRVWARNSMTimeCheck,
            TestStepDRVWARNSMTimeCheck,
            TestStepAPPDEMO_TONHTimeCheck,
            TestStepAPPDEMO_HMIHTimeCheck,
        ]  # in this list all the needed test steps are included


"""Functions to simplify the code."""


def create_mask(difference_between_timestamps, tolerance):
    """
    Creates a mask to verify if the values in the list are within 0 and the threshold.

    Parameters:
    difference_between_timestamps (list of float): The list of timestamp differences.
    tolerance (float): The threshold value.

    Returns:
    list of bool: A mask indicating whether each value is within the range.
    """
    return [0 < value <= tolerance for value in difference_between_timestamps]


def create_figures(time, time_list, difference_between_timestamps, cycle_time_ms, tolerance, signal_name):
    """
    Creates two figures: one with the signal and another with the differences between timestamps.

    Parameters:
    time (pandas.Series): The time values.
    time_list (pandas.Series): The signal values.
    difference_between_timestamps (pandas.Series): The differences between timestamps.
    cycle_time_ms (float): The cycle time constant.
    tolerance (float): The threshold value.
    signal_name (str): The name of the signal.

    Returns:
    tuple: (plotly.graph_objs._figure.Figure, plotly.graph_objs._figure.Figure) - The two figures.

    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=time,
            y=time_list,
            mode="lines",
            name=signal_name,
        )
    )

    fig.layout = go.Layout(
        yaxis=dict(tickformat="14"),
        xaxis=dict(tickformat="14"),
        xaxis_title="Time[ms]",
        title=f"Cycle times for {signal_name}",
    )
    fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)

    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            x=time_list,  # The x-axis (time)
            y=difference_between_timestamps,  # The difference between timestamps
            name=signal_name,  # The label for this trace
            marker=dict(
                color="blue", opacity=0.8, line=dict(width=1.5, color="blue")
            ),  # Specify bar color, opacity, and border
        )
    )

    # Adjust the layout for the bar chart
    fig2.layout = go.Layout(
        yaxis=dict(tickformat="14"),  # Format for the y-axis
        xaxis=dict(tickformat="14"),  # Format for the x-axis
        xaxis_title="Time[ms]",
        title="Differences between cycle times",  # Title of the chart
    )

    # Horizontal line for the threshold
    fig2.add_hline(
        y=cycle_time_ms,  # The y-coordinate for the horizontal line
        name="Threshold",
        line=dict(color="red", width=1.5),  # Style of the line
    )

    # Horizontal rectangle for highlighting the threshold region
    fig2.add_hrect(
        y0=(0 if cycle_time_ms - tolerance <= 0 else cycle_time_ms - tolerance),  # The bottom of the rectangle
        y1=tolerance,  # The top of the rectangle
        line_width=0,  # No border
        fillcolor="red",  # Fill color
        opacity=0.2,  # Transparency level
    )

    return fig, fig2


def evaluate_cycle_time(df, component_signal, component_constant):
    """
    Evaluates the cycle time based on the specified signal and updates the test result.

    Parameters:
    self: The instance of the class containing the readers and result attributes.
    component_signal (str): The signal column to evaluate.
    component_constant (float): The cycle time constant for the component.

    Returns:
    tuple: (str, str, bool) - A tuple containing the evaluation message, test result, and measured result.
    """
    sig_sum = {}  # Initializing the dictionary with data for final evaluation table
    time_series = df[component_signal] / constants.GeneralConstants.US_IN_MS
    time = df.index / constants.GeneralConstants.US_IN_MS
    first_non_zero_index = next((i for i, x in enumerate(time_series) if x != 0), None)
    if first_non_zero_index is not None:
        time_series = time_series[first_non_zero_index:]

    # Remove leading zeros
    time_series = time_series[time_series != 0]

    if time_series.empty:
        test_result = fc.NOT_ASSESSED
        measured_result = FALSE
        evaluation = "The evaluation is FAILED, the signal wasn't found."
        # component_signal_name = signals_obj._properties[component_signal][0]
        # sig_sum = sig_sum[component_signal_name] = evaluation
        # remark = "The signal wasn't found in the data."
        # sig_sum = fh.convert_dict_to_pandas(sig_sum, remark)
        # return [evaluation, test_result, measured_result, None, None]

    else:
        tolerance = component_constant + (component_constant * THRESHOLD_TIME_CONSTANTS.THRESHOLD)
        differences = time_series.diff().abs().dropna()
        if (differences <= tolerance).all():
            test_result = fc.PASS
            measured_result = TRUE
            evaluation = " ".join(
                f" The evaluation is PASSED, all differences between time cycles are between thresholds: \
                    0 and {tolerance} [ms].".split()
            )
        else:
            test_result = fc.FAIL
            measured_result = FALSE
            max_diff = round(differences.max(), 3)
            if (differences == 0).any() and (differences > tolerance).any():
                evaluation = " ".join(
                    f" The evaluation is FAILED, because not all differences between time cycles are between thresholds: \
                        0 and {tolerance} [ms]. The max value of difference being \
                        {max_diff} [ms] and also some differences are = 0 [ms].".split()
                )
            if (differences > tolerance).all():
                evaluation = " ".join(
                    f" The evaluation is FAILED, because all differences between time cycles are above the thresholds: \
                        {tolerance} [ms].".split()
                )
            elif (differences > tolerance).any():
                evaluation = " ".join(
                    f" The evaluation is FAILED, because some differences between time cycles are above the thresholds: \
                        {tolerance} [ms]. The max value of difference being \
                        {max_diff} [ms].".split()
                )
            elif (differences == 0).all():
                evaluation = " ".join(
                    f"The evaluation is FAILED, because the signal {component_signal} had all differences between cycle times = 0 [ms].".split()
                )

            elif (differences == 0).any():
                evaluation = " ".join(
                    f" The evaluation is FAILED, because the signal {component_signal} \
                        had differences between cycle times = 0 [ms].".split()
                )
            else:
                evaluation = " ".join(
                    f" The evaluation is FAILED, because not all differences between time cycles are between thresholds: \
                        0 and {tolerance} [ms]. The max value of difference being \
                        {max_diff} [ms] and also some differences are = 0 [ms].".split()
                )
    component_signal_name = signals_obj._properties[component_signal][0]
    sig_sum[component_signal_name] = evaluation
    remark = " ".join(
        f" THRESHOLD_UPPER_LIMIT({tolerance}) = CYCLE_TIME_MS({component_constant}) + (CYCLE_TIME_MS({component_constant}) * THRESHOLD({THRESHOLD_TIME_CONSTANTS.THRESHOLD})).".split()
    )
    fig, fig2 = create_figures(time, time_series, differences, component_constant, tolerance, component_signal)
    sig_sum = fh.convert_dict_to_pandas(sig_sum, remark)

    return [sig_sum, test_result, measured_result, fig, fig2]
