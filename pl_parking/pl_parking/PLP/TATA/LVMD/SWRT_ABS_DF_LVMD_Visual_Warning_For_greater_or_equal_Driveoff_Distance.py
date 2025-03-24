"""Example functional test"""  # this is a required docstring
import tempfile
from pathlib import Path

import pandas as pd

from tsf.core.utilities import debug

"""import libraries"""
import logging
import os
import sys

import numpy as np
import plotly.graph_objects as go

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRC_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", "..","..",".."))
if TRC_ROOT not in sys.path:
    sys.path.append(TRC_ROOT)
"""imports from tsf core"""
from tsf.core.results import DATA_NOK, FALSE, TRUE, BooleanResult
from tsf.core.testcase import (
    TestCase,
    TestStep,
    register_signals,
    testcase_definition,
    teststep_definition, verifies,
)
from tsf.io.signals import SignalDefinition

"""imports from current repo"""
import pl_parking.common_constants as fc
import pl_parking.common_ft_helper as fh
import pl_parking.PLP.MF.constants as constants
from pl_parking.common_ft_helper import MfCustomTestcaseReport, MfCustomTeststepReport
from pl_parking.PLP.TATA.LVMD.constants import ConstantsLVMD, WarningTrigger

__author__ = ""
__copyright__ = "2020-2012, Continental AG"
__version__ = ""
__status__ = "Production"

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ALIAS = "SWRT_ABS_DF_LVMD_Visual_Warning_For_greater_or_equal_Driveoff_Distance"


class Signals(SignalDefinition):
    class Columns(SignalDefinition.Columns):
        """Column defines."""

        TIME = "TimeStamp"
        SYSTEM_STATUS = "system status"
        WARNING_TRIGGER = 'system warning'
        NUM_VEH_IN_ROI = "number of VehiclesinROI"
        StandStill_Time = "standstill time"
        Driven_Distance = "driver off distance"

    def __init__(self):
        """Initialize the signal definition."""
        super().__init__()

        self._root = ["AP", "LVMD", "SI"]  # list of roots from a measurement

        self._properties = {
            self.Columns.TIME: [
                "Time",
                "Another version of signal",
            ],
            self.Columns.SYSTEM_STATUS: [
                ".StatusPort.lvmdSystemStatus_nu",
            ],
            self.Columns.WARNING_TRIGGER: [
                ".StatusPort.warningTriger",
            ],
            self.Columns.NUM_VEH_IN_ROI: [
                ".StatusPort.numVehiclesinROI_nu"
            ],
            self.Columns.StandStill_Time: [
                ".StatusPort.lvmdLeadVehicleStatus_nu.leadvehicle_standstilltime"
            ],
            self.Columns.Driven_Distance: [
                ".StatusPort.lvmdLeadVehicleStatus_nu.leadvehicle_driven_distance"
            ],
        }


signals_obj = Signals()

@teststep_definition(
    step_number=1,
    name="LVMD Visual Warning",  # this would be shown as a test step name in html report
    description="LVMD will activate/enable Visual warning for final tracked Lead vehicle with "
                "Drive off distance greater than or equal to LVMDs driveOff distance.",  # this would be shown as a
    # test step description in html report
    expected_result=BooleanResult(
        TRUE
    ),  # this expected result would be compared with measured_result and give a verdict
)
@register_signals(ALIAS, Signals)
class Driven_visual_warning(TestStep):

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
        time_threshold = None
        # signal_name = signals_obj._properties
        # Make a constant with the reader for signals:
        self.test_result = fc.INPUT_MISSING  # Result
        self.result.measured_result = DATA_NOK  # Initializing the result with data nok

        plot_titles, plots, remarks = fh.rep([], 3)

        signal_summary = {}  # Initializing the dictionary with data for final evaluation table

        signals = self.readers[ALIAS]
        signals[Signals.Columns.TIMESTAMP] = signals.index
        warning = signals[Signals.Columns.WARNING_TRIGGER]
        Driven_distance = signals[Signals.Columns.Driven_Distance]
        Driven_distance = np.array(Driven_distance)
        warning = np.array(warning)
        numVehinROI = signals[Signals.Columns.NUM_VEH_IN_ROI]
        numVehinROI = np.array(numVehinROI)


        if np.any(numVehinROI > 0):
            if np.any((Driven_distance >= ConstantsLVMD.LVMD_Alert_Min_DriveoffDistance_nu) &
                      (warning == WarningTrigger.LVMD_Trigger_VISUAL)):
                self.result.measured_result = TRUE
                eval_cond = True
                eval_text = ("There is activation of Visual warning "
                             "when driven distance of selected lead Vehicle satisfied LVMDs Drive Off Distance.")
            else:
                self.result.measured_result = FALSE
                eval_cond = False
                eval_text = "Driven Distance of selected lead Vehicle is less than LVMD's Drive Off Distance"
        else:
            self.result.measured_result = FALSE
            eval_cond = False
            eval_text = "There is no Target vehicle in ROI ."


        # Set table dataframe
        signal_summary = pd.DataFrame(
            {
                "Evaluation": {
                    "1": eval_cond,
                },
                "Result": {
                    "1": eval_text,
                },
            }
        )

        sig_sum = fh.build_html_table(signal_summary)
        plot_titles.append("")
        plots.append(sig_sum)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=signals[Signals.Columns.TIME].values.tolist(),
                y=signals[Signals.Columns.Driven_Distance].values.tolist(),
                mode="lines",
                name=".StatusPort.lvmdLeadVehicleStatus_nu.leadvehicle_driven_distance",
            )
        )
        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), yaxis_title="Driven Distance[m]", xaxis_title="Time [s]")
        fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
        plot_titles.append("Graphical Overview")
        plots.append(fig)
        remarks.append("")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=signals[Signals.Columns.TIME].values.tolist(),
                y=signals[Signals.Columns.WARNING_TRIGGER].values.tolist(),
                mode="lines",
                name=".StatusPort.warningTriger",
            )
        )
        fig.layout = go.Layout(yaxis=dict(tickformat="14"), xaxis=dict(tickformat="14"), yaxis_title="Warning trigger", xaxis_title="Time [s]")
        fig.update_layout(constants.PlotlyTemplate.lgt_tmplt)
        plot_titles.append("Graphical Overview")
        plots.append(fig)
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


# Define the test case definition. This will include the name of the test case and a description of the test.
@verifies("1300648")
@testcase_definition(
    name="SWRT_ABS_DF_LVMD_Visual_Warning_For_greater_or_equal_Driveoff_Distance",
    description=("LVMD will activate Visual Warning ."),
)
# Define the class for test case which will inherit the TestCase class and will return the test steps.
class Driven_visual_warning_enable(TestCase):
    """Example test case."""  # example of required docstring

    custom_report = MfCustomTestcaseReport

    @property
    def test_steps(self):
        """Returns the test steps."""  # example of required docstring
        return [Driven_visual_warning]  # in this list all the needed test steps are included


def main(data_folder: Path, temp_dir: Path = None, open_explorer=True):
    """Optional, call to debug to set up debugging in the simplest possible way.
    When calling the test case you need to provide a valid input to
    execute the test (e.g. a BSIG file) and report the result.
    This is only meant to jump start testcase debugging.
    """
    # Define your directory path to your measurements for debugging purposes
    test_bsigs = [r"D:\JenkinsServer_Main\workspace\FFL_CL_Simulation\package\tests\SIL\CarMaker\SimOutput\SWRT_ABS_DF_LVMD_Visual_Warning_For_greater_or_equal_Driveoff_Distance_1300648.erg"]
    debug(
        Driven_visual_warning_enable,
        *test_bsigs,
        temp_dir=temp_dir,
        open_explorer=open_explorer,
        kpi_report=False,
        dev_report=True,
    )
    _log.debug("All done.")



if __name__ == "__main__":
    import time
    timestr = time.strftime("%Y%m%d_%H%M%S")
    
    pat= r"\\cw01.contiwan.com\Root\Loc\blr3\didr2991\SYS230TM14\FFL_Reports\FFL_CL_Report_TATA_LVMD\FFL_CL"+timestr
    working_directory = Path(pat)

    with open(r"\\cw01.contiwan.com\Root\Loc\blr3\didr2991\SYS230TM14\FFL_Reports\FFL_CL_Report_TATA_LVMD\Jenkin_info.txt", "w") as f:
        
        contents = "".join(str(working_directory))
        f.write(contents)
        f.write("\n")


    data_folder = working_directory / "data"
    
    out_folder = working_directory / "out"
    
    
    main(data_folder=data_folder, temp_dir=out_folder, open_explorer=True)